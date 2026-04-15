"""
Modèle pour les notifications.
"""

from django.db import models
from django.utils import timezone

from .mixins import TimestampMixin
from .exceptions import NotificationException


class Notification(TimestampMixin):
    """
    Notification envoyée à un utilisateur.
    
    Attributs:
        utilisateur: Destinataire
        message: Contenu de la notification
        type_notification: Type (changement statut, RDV, etc.)
        lu: Si la notification a été lue
        date_envoi: Date d'envoi
        date_lecture: Date de lecture
    """
    
    class Type(models.TextChoices):
        CHANGEMENT_STATUT = 'changement_statut', 'Changement de statut'
        DOSSIER_PRET = 'dossier_pret', 'Dossier prêt'
        RDV_PROPOSE = 'rdv_propose', 'Rendez-vous proposé'
        RDV_CONFIRME = 'rdv_confirme', 'Rendez-vous confirmé'
        RDV_ANNULE = 'rdv_annule', 'Rendez-vous annulé'
        NOUVEAU_DOCUMENT = 'nouveau_document', 'Nouveau document'
        COMPTE_CREE = 'compte_cree', 'Compte créé'
        AUTRE = 'autre', 'Autre'

    id = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(
        'core.Utilisateur',
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name="Utilisateur"
    )
    message = models.TextField(verbose_name="Message")
    type_notification = models.CharField(
        max_length=50, 
        choices=Type.choices, 
        default=Type.AUTRE,
        verbose_name="Type"
    )
    lu = models.BooleanField(default=False, verbose_name="Lu")
    date_envoi = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date d'envoi"
    )
    date_lecture = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Date de lecture"
    )
    lien = models.URLField(
        null=True, 
        blank=True,
        verbose_name="Lien associé"
    )
    icon = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        verbose_name="Icône",
        help_text="Classe CSS ou nom d'icône"
    )

    class Meta:
        db_table = 'notifications'
        ordering = ['-date_envoi']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['utilisateur', 'lu']),
            models.Index(fields=['date_envoi']),
            models.Index(fields=['type_notification']),
        ]

    def __str__(self) -> str:
        return f"Notification pour {self.utilisateur.nom_complet}: {self.message[:50]}..."
    
    def __repr__(self) -> str:
        return f"<Notification: {self.id} - {self.type_notification} - Lu: {self.lu}>"
    
    # ========== Propriétés ==========
    
    @property
    def est_recente(self) -> bool:
        """Vérifie si la notification est récente (< 24h)."""
        return (timezone.now() - self.date_envoi).days < 1
    
    @property
    def temps_ecoule(self) -> str:
        """Retourne le temps écoulé depuis l'envoi."""
        delta = timezone.now() - self.date_envoi
        
        if delta.days == 0:
            hours = delta.seconds // 3600
            if hours == 0:
                minutes = delta.seconds // 60
                return f"{minutes} min" if minutes > 0 else "À l'instant"
            return f"{hours}h"
        elif delta.days == 1:
            return "Hier"
        elif delta.days < 7:
            return f"{delta.days} jours"
        else:
            return self.date_envoi.strftime('%d/%m/%Y')
    
    @property
    def icon_par_defaut(self) -> str:
        """Retourne l'icône par défaut selon le type."""
        icons = {
            self.Type.CHANGEMENT_STATUT: 'status',
            self.Type.DOSSIER_PRET: 'folder-check',
            self.Type.RDV_PROPOSE: 'calendar-plus',
            self.Type.RDV_CONFIRME: 'calendar-check',
            self.Type.RDV_ANNULE: 'calendar-x',
            self.Type.NOUVEAU_DOCUMENT: 'file-plus',
            self.Type.COMPTE_CREE: 'user-plus',
            self.Type.AUTRE: 'bell',
        }
        return icons.get(self.type_notification, 'bell')
    
    # ========== Méthodes métier ==========
    
    def marquer_lu(self):
        """Marque la notification comme lue."""
        if not self.lu:
            self.lu = True
            self.date_lecture = timezone.now()
            self.save(update_fields=['lu', 'date_lecture'])
    
    def marquer_non_lu(self):
        """Marque la notification comme non lue."""
        if self.lu:
            self.lu = False
            self.date_lecture = None
            self.save(update_fields=['lu', 'date_lecture'])
    
    # ========== Méthodes de classe ==========
    
    @classmethod
    def envoyer(cls, utilisateur, message: str, type_notif: str = 'autre', 
                lien: str = None, icon: str = None):
        """
        Envoie une notification à un utilisateur.
        
        Args:
            utilisateur: Destinataire
            message: Contenu
            type_notif: Type de notification
            lien: Lien associé (optionnel)
            icon: Icône personnalisée (optionnel)
            
        Returns:
            Notification: La notification créée
        """
        try:
            return cls.objects.create(
                utilisateur=utilisateur,
                message=message,
                type_notification=type_notif,
                lien=lien,
                icon=icon
            )
        except Exception as e:
            raise NotificationException(
                f"Erreur lors de l'envoi: {str(e)}",
                NotificationException.ENVOI_ECHOUE,
                utilisateur.id
            )
    
    @classmethod
    def envoyer_a_tous(cls, utilisateurs, message: str, type_notif: str = 'autre'):
        """
        Envoie une notification à plusieurs utilisateurs (bulk create).
        
        Args:
            utilisateurs: Liste ou QuerySet d'utilisateurs
            message: Contenu
            type_notif: Type de notification
            
        Returns:
            list: Notifications créées
        """
        notifications = [
            cls(utilisateur=u, message=message, type_notification=type_notif)
            for u in utilisateurs
        ]
        return cls.objects.bulk_create(notifications)
    
    @classmethod
    def envoyer_aux_agents(cls, message: str, type_notif: str = 'autre'):
        """Envoie une notification à tous les agents."""
        from .utilisateur import Utilisateur
        agents = Utilisateur.objects.filter(role=Utilisateur.Role.AGENT, is_active=True)
        return cls.envoyer_a_tous(agents, message, type_notif)
    
    @classmethod
    def envoyer_aux_admins(cls, message: str, type_notif: str = 'autre'):
        """Envoie une notification à tous les administrateurs."""
        from .utilisateur import Utilisateur
        admins = Utilisateur.objects.filter(
            role=Utilisateur.Role.ADMINISTRATEUR, 
            is_active=True
        )
        return cls.envoyer_a_tous(admins, message, type_notif)
    
    @classmethod
    def non_lues(cls, utilisateur_id: int = None):
        """Retourne les notifications non lues."""
        qs = cls.objects.filter(lu=False)
        if utilisateur_id:
            qs = qs.filter(utilisateur_id=utilisateur_id)
        return qs
    
    @classmethod
    def marquer_tout_lu(cls, utilisateur_id: int):
        """Marque toutes les notifications d'un utilisateur comme lues."""
        return cls.objects.filter(
            utilisateur_id=utilisateur_id, 
            lu=False
        ).update(
            lu=True, 
            date_lecture=timezone.now()
        )
    
    @classmethod
    def supprimer_anciennes(cls, jours: int = 30):
        """Supprime les notifications de plus de X jours."""
        from datetime import timedelta
        date_limite = timezone.now() - timedelta(days=jours)
        return cls.objects.filter(date_envoi__lt=date_limite).delete()
    
    @classmethod
    def statistiques(cls, utilisateur_id: int = None):
        """Statistiques des notifications."""
        from django.db.models import Count
        
        qs = cls.objects
        if utilisateur_id:
            qs = qs.filter(utilisateur_id=utilisateur_id)
        
        return {
            'total': qs.count(),
            'non_lues': qs.filter(lu=False).count(),
            'par_type': qs.values('type_notification').annotate(total=Count('id')),
        }
