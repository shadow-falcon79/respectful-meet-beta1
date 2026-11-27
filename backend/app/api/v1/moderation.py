from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.block import Block
from app.models.report import Report
from app.models.user import User
from app.schemas.moderation import BlockIn, BlockOut, ReportIn, ReportOut

router = APIRouter(tags=["moderation"])


@router.post("/blocks", response_model=BlockOut, status_code=status.HTTP_201_CREATED)
def block_user(payload: BlockIn, current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> BlockOut:
    if payload.user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot block yourself")

    target = db.query(User).filter(User.id == payload.user_id).first()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = (
        db.query(Block).filter(Block.blocker_id == current_user.id, Block.blocked_id == payload.user_id).first()
    )
    if existing is not None:
        return existing  # idempotent

    block = Block(blocker_id=current_user.id, blocked_id=payload.user_id)
    db.add(block)
    try:
        db.commit()
    except IntegrityError:
        # Concurrent double-tap/retry raced past the `existing is None`
        # check above. The unique constraint on (blocker_id, blocked_id)
        # is the real guard; make the response idempotent instead of a 500.
        db.rollback()
        existing = (
            db.query(Block).filter(Block.blocker_id == current_user.id, Block.blocked_id == payload.user_id).first()
        )
        if existing is None:
            raise
        return existing
    db.refresh(block)
    return block


@router.delete("/blocks/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unblock_user(user_id: str, current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> None:
    block = db.query(Block).filter(Block.blocker_id == current_user.id, Block.blocked_id == user_id).first()
    if block is not None:
        db.delete(block)
        db.commit()


@router.get("/blocks", response_model=list[BlockOut])
def list_blocked_users(current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> list[BlockOut]:
    return db.query(Block).filter(Block.blocker_id == current_user.id).all()


@router.post("/reports", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def report_user(payload: ReportIn, current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> ReportOut:
    if payload.reported_user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot report yourself")

    target = db.query(User).filter(User.id == payload.reported_user_id).first()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    report = Report(
        reporter_id=current_user.id,
        reported_user_id=payload.reported_user_id,
        message_id=payload.message_id,
        reason=payload.reason,
        details=payload.details,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return ReportOut(id=report.id, reported_user_id=report.reported_user_id, reason=report.reason, status=report.status.value, created_at=report.created_at)
