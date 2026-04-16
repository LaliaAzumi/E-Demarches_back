from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification


@shared_task
def envoyer_email_notification(notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, type_notification='email')
        send_mail(
            subject=notification.sujet,
            message=notification.contenu,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.destinataire.email],
            fail_silently=False,
        )
        notification.statut = 'sent'
        from django.utils import timezone
        notification.date_envoi = timezone.now()
        notification.save()
        return f"Email envoyé à {notification.destinataire.email}"
    except Exception as e:
        notification.statut = 'failed'
        notification.erreur = str(e)
        notification.save()
        return f"Erreur: {str(e)}"
