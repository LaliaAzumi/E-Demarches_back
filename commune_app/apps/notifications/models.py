from django.db import models
from apps.users.models import Utilisateur


class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        db_column='utilisateur_id'
    )
    message = models.TextField()
    lu = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(auto_now_add=True, db_column='date_envoi')

    class Meta:
        db_table = 'notifications'
        ordering = ['-date_envoi']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['utilisateur', 'lu']),
            models.Index(fields=['date_envoi']),
        ]

    def __str__(self):
        return f"Notification pour {self.utilisateur.nom}"
