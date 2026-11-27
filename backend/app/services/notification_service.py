from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.notification import Notification, NotificationDevice, NotificationType

# Product copy is intentionally short; locale is selected from the user's device subscription.
TEMPLATES={
"EN":{"WELCOME":("Welcome to Respectful Meet","Complete your profile and discover how Respectful Meet works."),"GUIDANCE":("A quick Respectful Meet tip","Complete your profile, use clear photos and explore profiles regularly to improve your experience."),"SAFETY":("Stay safe","Never send money or sensitive financial information to someone you meet online."),"REENGAGEMENT":("We saved your place","Come back when you have a moment and see what's new on Respectful Meet."),"ANNOUNCEMENT":("Respectful Meet","We have something new to share with you.")},
"FR":{"WELCOME":("Bienvenue sur Respectful Meet","Complétez votre profil et découvrez comment utiliser Respectful Meet."),"GUIDANCE":("Un conseil Respectful Meet","Complétez votre profil, utilisez de belles photos et découvrez régulièrement de nouveaux profils."),"SAFETY":("Restez prudent","N'envoyez jamais d'argent ni d'informations financières sensibles à une personne rencontrée en ligne."),"REENGAGEMENT":("Votre espace vous attend","Revenez quand vous avez un moment pour découvrir ce qui est nouveau sur Respectful Meet."),"ANNOUNCEMENT":("Respectful Meet","Nous avons une nouvelle information à partager avec vous.")},
"ES":{"WELCOME":("Bienvenido a Respectful Meet","Completa tu perfil y descubre cómo funciona Respectful Meet."),"GUIDANCE":("Consejo de Respectful Meet","Completa tu perfil, usa buenas fotos y descubre perfiles con frecuencia."),"SAFETY":("Mantente seguro","Nunca envíes dinero ni información financiera sensible a alguien que conociste en línea."),"REENGAGEMENT":("Tu espacio te espera","Vuelve cuando tengas un momento para descubrir novedades."),"ANNOUNCEMENT":("Respectful Meet","Tenemos una novedad para compartir contigo.")},
"PT":{"WELCOME":("Bem-vindo ao Respectful Meet","Complete o seu perfil e descubra como o Respectful Meet funciona."),"GUIDANCE":("Dica do Respectful Meet","Complete o seu perfil, use boas fotos e descubra novos perfis regularmente."),"SAFETY":("Mantenha-se seguro","Nunca envie dinheiro ou informações financeiras sensíveis a alguém que conheceu online."),"REENGAGEMENT":("O seu espaço está à espera","Volte quando tiver um momento para descobrir novidades."),"ANNOUNCEMENT":("Respectful Meet","Temos uma novidade para partilhar consigo.")},
"DE":{"WELCOME":("Willkommen bei Respectful Meet","Vervollständige dein Profil und entdecke die wichtigsten Funktionen."),"GUIDANCE":("Respectful Meet Tipp","Vervollständige dein Profil, nutze gute Fotos und entdecke regelmäßig neue Profile."),"SAFETY":("Bleib sicher","Sende niemals Geld oder sensible Finanzdaten an Personen, die du online kennenlernst."),"REENGAGEMENT":("Dein Platz wartet","Komm zurück und entdecke, was es Neues gibt."),"ANNOUNCEMENT":("Respectful Meet","Wir haben Neuigkeiten für dich.")},
"IT":{"WELCOME":("Benvenuto su Respectful Meet","Completa il tuo profilo e scopri come funziona l'app."),"GUIDANCE":("Consiglio Respectful Meet","Completa il profilo, usa buone foto e scopri regolarmente nuovi profili."),"SAFETY":("Resta al sicuro","Non inviare mai denaro o dati finanziari sensibili a persone conosciute online."),"REENGAGEMENT":("Il tuo spazio ti aspetta","Torna quando hai un momento e scopri le novità."),"ANNOUNCEMENT":("Respectful Meet","Abbiamo una novità da condividere con te.")},
"RU":{"WELCOME":("Добро пожаловать в Respectful Meet","Заполните профиль и узнайте, как пользоваться приложением."),"GUIDANCE":("Совет Respectful Meet","Заполните профиль, добавьте хорошие фото и регулярно просматривайте новые анкеты."),"SAFETY":("Будьте осторожны","Никогда не отправляйте деньги или важные финансовые данные знакомым из интернета."),"REENGAGEMENT":("Мы вас ждём","Вернитесь, когда будет удобно, и посмотрите новые возможности."),"ANNOUNCEMENT":("Respectful Meet","У нас есть новости для вас.")},
"ZH":{"WELCOME":("欢迎使用 Respectful Meet","完善个人资料，了解如何使用 Respectful Meet。"),"GUIDANCE":("Respectful Meet 小贴士","完善资料、使用清晰照片，并经常发现新的个人资料。"),"SAFETY":("请注意安全","不要向网络认识的人汇款或提供敏感的财务信息。"),"REENGAGEMENT":("等你回来","有空时回来看看 Respectful Meet 的新内容。"),"ANNOUNCEMENT":("Respectful Meet","我们有新的消息与你分享。")},
"JA":{"WELCOME":("Respectful Meetへようこそ","プロフィールを完成させ、アプリの使い方を確認しましょう。"),"GUIDANCE":("Respectful Meetのヒント","プロフィールを充実させ、分かりやすい写真を使い、新しいプロフィールを定期的に見てみましょう。"),"SAFETY":("安全に利用しましょう","オンラインで知り合った人に送金したり、重要な金融情報を渡したりしないでください。"),"REENGAGEMENT":("また会いましょう","時間があるときに戻ってきて、新しいプロフィールを確認しましょう。"),"ANNOUNCEMENT":("Respectful Meet","新しいお知らせがあります。")},
"TR":{"WELCOME":("Respectful Meet'e hoş geldiniz","Profilinizi tamamlayın ve uygulamayı nasıl kullanacağınızı keşfedin."),"GUIDANCE":("Respectful Meet ipucu","Profilinizi tamamlayın, iyi fotoğraflar kullanın ve yeni profilleri düzenli olarak keşfedin."),"SAFETY":("Güvende kalın","İnternette tanıştığınız kişilere asla para veya hassas finansal bilgiler göndermeyin."),"REENGAGEMENT":("Sizi bekliyoruz","Uygun olduğunuzda geri dönün ve yenilikleri keşfedin."),"ANNOUNCEMENT":("Respectful Meet","Sizinle paylaşmak istediğimiz yeni bir haber var.")},
"AR":{"WELCOME":("مرحباً بك في Respectful Meet","أكمل ملفك الشخصي وتعرّف على طريقة استخدام التطبيق."),"GUIDANCE":("نصيحة من Respectful Meet","أكمل ملفك وأضف صوراً واضحة واكتشف ملفات جديدة بانتظام."),"SAFETY":("حافظ على سلامتك","لا ترسل المال أو المعلومات المالية الحساسة إلى أشخاص تعرفت عليهم عبر الإنترنت."),"REENGAGEMENT":("ننتظرك","عد عندما يتوفر لديك وقت واكتشف ما هو جديد."),"ANNOUNCEMENT":("Respectful Meet","لدينا معلومات جديدة نود مشاركتها معك.")},
}

EVENT_TEMPLATES = {
    "LIKE": ("New like", "Someone liked your profile."),
    "MATCH": ("New match", "You have a new match."),
    "MESSAGE": ("New message", "You have a new message."),
    "PAYMENT": ("Premium activated", "Your Premium subscription is now active."),
    "SUBSCRIPTION_EXPIRING": ("Premium expiring soon", "Your Premium subscription expires soon."),
    "REPORT": ("Safety update", "Your report has been received or updated."),
    "SYSTEM": ("Respectful Meet", "You have a new notification."),
}

def _copy(lang, kind):
    lang = (lang or "EN").upper()
    return TEMPLATES.get(lang, TEMPLATES["EN"]).get(kind, EVENT_TEMPLATES.get(kind, TEMPLATES["EN"].get(kind, EVENT_TEMPLATES.get(kind, ("Respectful Meet", "You have a new notification.")))))

def _recipient_language(db, user_id: str) -> str:
    device = (db.query(NotificationDevice)
              .filter(NotificationDevice.user_id == user_id)
              .order_by(NotificationDevice.last_seen_at.desc())
              .first())
    return device.language if device else "EN"

def create_notification(db,user_id,kind:NotificationType,title=None,body=None,language=None):
    if title is None or body is None:
        t,b=_copy(language or _recipient_language(db, user_id),kind.value)
        title=title or t; body=body or b
    n=Notification(user_id=user_id,type=kind,title=title,body=body); db.add(n); db.flush(); return n

def unread_count(db,user_id): return db.query(Notification).filter(Notification.user_id==user_id,Notification.is_read.is_(False)).count()

def send_push_to_device(device:NotificationDevice,title:str,body:str)->bool:
    if not settings.vapid_private_key or not settings.vapid_subject: return False
    try:
        from pywebpush import webpush
        webpush(subscription_info={"endpoint":device.endpoint,"keys":{"p256dh":device.p256dh,"auth":device.auth}},data=__import__('json').dumps({"title":title,"body":body}),vapid_private_key=settings.vapid_private_key,vapid_claims={"sub":settings.vapid_subject})
        return True
    except Exception:
        return False

def deliver_push(db, notification):
    devices=db.query(NotificationDevice).filter(NotificationDevice.user_id==notification.user_id).all(); sent=False
    for d in devices:
        if send_push_to_device(d,notification.title,notification.body or ""):
            sent=True
    if sent: notification.push_sent_at=datetime.now(timezone.utc)
    return sent

def user_local_hour(device):
    try:return datetime.now(ZoneInfo(device.timezone)).hour
    except Exception:return datetime.now(timezone.utc).hour

def daily_engagement(db, now=None):
    """At most 10 communications/user/day; event notifications are not counted here."""
    now=now or datetime.now(timezone.utc); users=db.query(NotificationDevice.user_id).distinct().all(); made=0
    for (uid,) in users:
        devices=db.query(NotificationDevice).filter(NotificationDevice.user_id==uid).order_by(NotificationDevice.last_seen_at.desc()).all()
        if not devices: continue
        d=devices[0]; local_hour=user_local_hour(d)
        # Send only in normal waking/phone-use windows; scheduler can run every hour.
        if local_hour not in {8,10,13,16,19,21}: continue
        start=now-timedelta(hours=24)
        count=db.query(Notification).filter(Notification.user_id==uid,Notification.type.in_([NotificationType.GUIDANCE,NotificationType.WELCOME,NotificationType.REENGAGEMENT,NotificationType.ANNOUNCEMENT]),Notification.created_at>=start).count()
        if count>=10: continue
        last=db.query(Notification).filter(Notification.user_id==uid,Notification.type.in_([NotificationType.GUIDANCE,NotificationType.WELCOME,NotificationType.REENGAGEMENT]),Notification.created_at>=start).order_by(Notification.created_at.desc()).first()
        if last and (now-last.created_at).total_seconds()<3*3600: continue
        inactive=(now-d.last_seen_at).total_seconds()>48*3600
        kind=NotificationType.REENGAGEMENT if inactive else NotificationType.GUIDANCE
        n=create_notification(db,uid,kind)
        deliver_push(db,n); made+=1
    db.commit(); return made
