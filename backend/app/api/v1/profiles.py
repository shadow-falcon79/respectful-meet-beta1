from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.rate_limit import UPLOAD_LIMIT, limiter
from app.models.photo import Photo
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import PhotoOut, ProfileOut, ProfileUpdateIn
from app.services.storage_service import MAX_IMAGE_SIZE_BYTES, StorageValidationError, get_storage_service
from app.services.photo_moderation_service import get_photo_moderation_service
from app.services.content_filter import find_violation

router = APIRouter(prefix="/profiles", tags=["profiles"])

MAX_PHOTOS_PER_PROFILE = 3


def _serialize_profile(profile: Profile, photos: list[Photo]) -> ProfileOut:
    storage = get_storage_service()
    ordered = sorted(photos, key=lambda p: (not p.is_primary, p.display_order))
    return ProfileOut(
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        date_of_birth=profile.date_of_birth,
        gender=profile.gender,
        country=profile.country,
        city=profile.city,
        bio=profile.bio,
        interests=profile.interests,
        photos=[
            PhotoOut(id=p.id, url=storage.url_for(p.storage_key), is_primary=p.is_primary, display_order=p.display_order)
            for p in ordered
        ],
    )


def _get_own_profile(db: DbSession, user: User) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.get("/me", response_model=ProfileOut)
def get_my_profile(current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> ProfileOut:
    profile = _get_own_profile(db, current_user)
    photos = db.query(Photo).filter(Photo.user_id == current_user.id).all()
    return _serialize_profile(profile, photos)


@router.patch("/me", response_model=ProfileOut)
def update_my_profile(
    payload: ProfileUpdateIn,
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> ProfileOut:
    profile = _get_own_profile(db, current_user)
    updates = payload.model_dump(exclude_unset=True)

    # Unlike messages (E2EE — see app/services/content_filter.py docstring),
    # the bio is plaintext and public, so this is the one place the
    # off-platform-contact filter can actually run server-side. Otherwise
    # a phone number or "add me on WhatsApp" in a bio would bypass the
    # restriction entirely, in plain view of every user who views the profile.
    bio = updates.get("bio")
    if bio:
        violation = find_violation(bio)
        if violation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bio cannot contain contact details or external links ({violation})",
            )

    for field, value in updates.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    photos = db.query(Photo).filter(Photo.user_id == current_user.id).all()
    return _serialize_profile(profile, photos)


@router.post("/me/photos", response_model=PhotoOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(UPLOAD_LIMIT)
async def upload_photo(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
) -> PhotoOut:
    existing = db.query(Photo).filter(Photo.user_id == current_user.id).all()
    if len(existing) >= MAX_PHOTOS_PER_PROFILE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {MAX_PHOTOS_PER_PROFILE} photos reached",
        )

    # Bounded read: never buffer more than the max allowed size + 1 byte into
    # memory, regardless of what the client claims or sends (DoS hardening —
    # matches the pattern already used for chat media in messages.py).
    content = await file.read(MAX_IMAGE_SIZE_BYTES + 1)
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 8MB)")

    moderation = get_photo_moderation_service().screen(content, file.content_type or "")
    if not moderation.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Photo rejected by content moderation ({moderation.reason or 'policy violation'})",
        )

    storage = get_storage_service()
    try:
        storage_key = storage.save(content, file.content_type or "", folder=f"profiles/{current_user.id}")
    except StorageValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    photo = Photo(
        user_id=current_user.id,
        storage_key=storage_key,
        is_primary=len(existing) == 0,  # first photo uploaded becomes primary automatically
        display_order=len(existing),
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)

    return PhotoOut(id=photo.id, url=storage.url_for(photo.storage_key), is_primary=photo.is_primary, display_order=photo.display_order)


@router.delete("/me/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(photo_id: str, current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> None:
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    was_primary = photo.is_primary
    storage_key = photo.storage_key
    db.delete(photo)
    db.commit()

    get_storage_service().delete(storage_key)

    if was_primary:
        next_photo = (
            db.query(Photo)
            .filter(Photo.user_id == current_user.id)
            .order_by(Photo.display_order)
            .first()
        )
        if next_photo is not None:
            next_photo.is_primary = True
            db.commit()


@router.patch("/me/photos/{photo_id}/primary", response_model=PhotoOut)
def set_primary_photo(photo_id: str, current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> PhotoOut:
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == current_user.id).first()
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    db.query(Photo).filter(Photo.user_id == current_user.id).update({"is_primary": False})
    photo.is_primary = True
    db.commit()
    db.refresh(photo)

    storage = get_storage_service()
    return PhotoOut(id=photo.id, url=storage.url_for(photo.storage_key), is_primary=True, display_order=photo.display_order)
