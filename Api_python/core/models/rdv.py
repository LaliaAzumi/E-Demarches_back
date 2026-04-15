"""
Modèles pour les rendez-vous et propositions.
"""

from datetime import datetime, date, time

from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .mixins import TimestampMixin
from .exceptions import RDVException, ValidationException


class PropositionRDV(TimestampMixin):
    """
    Proposition de créneau rendez-vous par un agent.
    
    Attributs:
        demande: Demande concernée
        agent: Agent ayant proposé
        date: Date du rendez-vous
        heure: Heure du rendez-vous
        lieu: Lieu de rendez-vous
        statut: Statut de la proposition
    """
    
    class Statut(models.TextChoices):
        PROPOSE = 'propose', 'Proposé'
        CHOISI = 'choisi', 'Choisi'
        REFUSE = 'refuse', 'Refusé'
        EXPIRE = 'expire', 'Expiré'

    id = models.AutoField(primary_key=True)
    demande = models.ForeignKey(
        'core.DemandeAdministrative',
        on_delete=models.CASCADE, 
        related_name='propositions_rdv',
        verbose_name="Demande"
    )
    agent = models.ForeignKey(
        'core.AgentAdministratif',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='propositions_rdv',
        verbose_name="Agent"
    )
    date = models.DateField(verbose_name="Date")
    heure = models.TimeField(verbose_name="Heure")
    lieu = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        verbose_name="Lieu"
    )
    statut = models.CharField(
        max_length=20, 
        choices=Statut.choices, 
        default=Statut.PROPOSE,
        verbose_name="Statut"
    )

    class Meta:
        db_table = 'propositions_rdv'
        verbose_name = 'Proposition de RDV'
        verbose_name_plural = 'Propositions de RDV'
        ordering = ['date', 'heure']
        # Empêcher les doublons de créneaux pour la même demande
        constraints = [
            models.UniqueConstraint(
                fields=['demande', 'date', 'heure'],
                name='unique_creneau_demande'
            )
        ]

    def __str__(self) -> str:
        return f"RDV le {self.date} à {self.heure}"
    
    def __repr__(self) -> str:
        return f"<PropositionRDV: {self.date} {self.heure} - {self.statut}>"
    
    # ========== Propriétés ==========
    
    @property
    def datetime_complet(self) -> datetime:
        """Retourne le datetime complet."""
        return datetime.combine(self.date, self.heure)
    
    @property
    def est_disponible(self) -> bool:
        """Vérifie si la proposition est encore disponible."""
        return self.statut == self.Statut.PROPOSE and not self.est_expire
    
    @property
    def est_expire(self) -> bool:
        """Vérifie si la proposition est expirée."""
        now = timezone.now()
        proposition_datetime = timezone.make_aware(
            self.datetime_complet,
            timezone.get_current_timezone()
        ) if timezone.is_naive(self.datetime_complet) else self.datetime_complet
        return proposition_datetime < now
    
    @property
    def est_choisi(self) -> bool:
        """Vérifie si cette proposition a été choisie."""
        return self.statut == self.Statut.CHOISI
    
    # ========== Validation ==========
    
    def clean(self):
        """Validation avant sauvegarde."""
        super().clean()
        
        # Vérifier que la date n'est pas dans le passé
        if self.date < timezone.now().date():
            raise ValidationException(
                "La date du rendez-vous ne peut pas être dans le passé",
                field='date'
            )
    
    # ========== Méthodes métier ==========
    
    def marquer_choisi(self):
        """
        Marque cette proposition comme choisie et refuse les autres.
        
        Raises:
            RDVException: Si la proposition n'est pas disponible
        """
        if not self.est_disponible:
            raise RDVException(
                "Cette proposition n'est plus disponible",
                RDVException.PROPOSITION_INVALIDE,
                str(self.date),
                str(self.heure)
            )
        
        with transaction.atomic():
            self.statut = self.Statut.CHOISI
            self.save()
            
            # Refuser les autres propositions de la même demande
            PropositionRDV.objects.filter(
                demande=self.demande
            ).exclude(id=self.id).update(statut=self.Statut.REFUSE)
    
    def marquer_expire(self):
        """Marque la proposition comme expirée."""
        if self.est_expire and self.statut == self.Statut.PROPOSE:
            self.statut = self.Statut.EXPIRE
            self.save(update_fields=['statut'])
    
    def refuser(self):
        """Refuse cette proposition."""
        if self.statut == self.Statut.PROPOSE:
            self.statut = self.Statut.REFUSE
            self.save(update_fields=['statut'])
    
    # ========== Méthodes de classe ==========
    
    @classmethod
    def propositions_actives(cls):
        """Retourne les propositions encore valides."""
        today = timezone.now().date()
        return cls.objects.filter(
            statut=cls.Statut.PROPOSE,
            date__gte=today
        )
    
    @classmethod
    def marquer_expires(cls):
        """Marque automatiquement les propositions expirées."""
        now = timezone.now()
        expired = cls.objects.filter(
            statut=cls.Statut.PROPOSE,
            date__lt=now.date()
        ) | cls.objects.filter(
            statut=cls.Statut.PROPOSE,
            date=now.date(),
            heure__lt=now.time()
        )
        count = expired.update(statut=cls.Statut.EXPIRE)
        return count


class RendezVous(TimestampMixin):
    """
    Rendez-vous confirmé (créé quand un citoyen choisit une proposition).
    
    Attributs:
        id_rendez_vous: Identifiant unique
        proposition: Proposition choisie
        citoyen: Citoyen concerné
        statut: Statut du rendez-vous
        date_confirmation: Date de confirmation
    """
    
    class Statut(models.TextChoices):
        CONFIRME = 'confirme', 'Confirmé'
        ANNULE = 'annule', 'Annulé'
        TERMINE = 'termine', 'Terminé'
        NO_SHOW = 'no_show', 'Absent'

    id = models.AutoField(primary_key=True)
    id_rendez_vous = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True,
        verbose_name="ID du rendez-vous"
    )
    proposition = models.OneToOneField(
        PropositionRDV,
        on_delete=models.CASCADE, 
        related_name='rendez_vous',
        verbose_name="Proposition"
    )
    citoyen = models.ForeignKey(
        'core.Citoyen',
        on_delete=models.CASCADE, 
        related_name='rendez_vous',
        verbose_name="Citoyen"
    )
    statut = models.CharField(
        max_length=20, 
        choices=Statut.choices, 
        default=Statut.CONFIRME,
        verbose_name="Statut"
    )
    date_confirmation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de confirmation"
    )
    notes = models.TextField(
        null=True, 
        blank=True,
        verbose_name="Notes"
    )

    class Meta:
        db_table = 'rendez_vous'
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        ordering = ['-date_confirmation']

    def __str__(self) -> str:
        return f"RDV #{self.id_rendez_vous or self.id} - {self.proposition.date}"
    
    def __repr__(self) -> str:
        return f"<RendezVous: {self.id_rendez_vous} - {self.statut}>"
    
    # ========== Sauvegarde ==========
    
    def save(self, *args, **kwargs):
        """Génère l'ID unique avant sauvegarde."""
        if not self.id_rendez_vous:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.id_rendez_vous = f"RDV-{timestamp}-{self.citoyen.id}"
        super().save(*args, **kwargs)
    
    # ========== Propriétés ==========
    
    @property
    def date_rdv(self) -> date:
        """Retourne la date du rendez-vous."""
        return self.proposition.date
    
    @property
    def heure_rdv(self) -> time:
        """Retourne l'heure du rendez-vous."""
        return self.proposition.heure
    
    @property
    def lieu_rdv(self) -> str:
        """Retourne le lieu du rendez-vous."""
        return self.proposition.lieu
    
    @property
    def agent_rdv(self):
        """Retourne l'agent responsable."""
        return self.proposition.agent
    
    @property
    def datetime_rdv(self) -> datetime:
        """Retourne le datetime complet du rendez-vous."""
        return self.proposition.datetime_complet
    
    @property
    
    def est_passe(self) -> bool:
        """Vérifie si le rendez-vous est passé."""
        return self.datetime_rdv < timezone.now()
    
    @property
    def peut_annuler(self) -> bool:
        """Vérifie si le rendez-vous peut être annulé."""
        return self.statut == self.Statut.CONFIRME and not self.est_passe
    
    # ========== Méthodes métier ==========
    
    def annuler(self, raison: str = None, par_citoyen: bool = True):
        """
        Annule le rendez-vous.
        
        Args:
            raison: Raison de l'annulation
            par_citoyen: True si annulé par le citoyen, False si par l'agent
            
        Raises:
            RDVException: Si le rendez-vous ne peut pas être annulé
        """
        if not self.peut_annuler:
            raise RDVException(
                "Ce rendez-vous ne peut plus être annulé",
                RDVException.RDV_EXPIRE
            )
        
        self.statut = self.Statut.ANNULE
        self.notes = f"Annulé {'par le citoyen' if par_citoyen else 'par l\'agent'}. {raison or ''}"
        self.save()
        
        # Notifier
        self._notifier_annulation(raison, par_citoyen)
    
    def _notifier_annulation(self, raison: str, par_citoyen: bool):
        """Envoie une notification d'annulation."""
        from .notifications import Notification
        
        if par_citoyen:
            # Notifier l'agent
            if self.agent_rdv:
                Notification.objects.create(
                    utilisateur=self.agent_rdv.utilisateur,
                    type_notification=Notification.Type.RDV_CONFIRME,
                    message=f"Le citoyen a annulé le RDV du {self.date_rdv}. {raison or ''}"
                )
        else:
            # Notifier le citoyen
            Notification.objects.create(
                utilisateur=self.citoyen.utilisateur,
                type_notification=Notification.Type.RDV_CONFIRME,
                message=f"Votre rendez-vous du {self.date_rdv} a été annulé. {raison or ''}"
            )
    
    def terminer(self, notes: str = None):
        """
        Marque le rendez-vous comme terminé.
        
        Args:
            notes: Notes sur le déroulement
        """
        self.statut = self.Statut.TERMINE
        if notes:
            self.notes = notes
        self.save(update_fields=['statut', 'notes', 'updated_at'])
    
    def marquer_no_show(self):
        """Marque le citoyen comme absent."""
        self.statut = self.Statut.NO_SHOW
        self.save(update_fields=['statut'])
    
    def modifier_lieu(self, nouveau_lieu: str):
        """Modifie le lieu du rendez-vous."""
        self.proposition.lieu = nouveau_lieu
        self.proposition.save(update_fields=['lieu'])
    
    # ========== Méthodes de classe ==========
    
    @classmethod
    def rdv_du_jour(cls, date_jour: date = None):
        """Retourne les rendez-vous d'une date."""
        date_jour = date_jour or timezone.now().date()
        return cls.objects.filter(
            proposition__date=date_jour,
            statut=cls.Statut.CONFIRME
        )
    
    @classmethod
    def rdv_a_venir(cls):
        """Retourne les rendez-vous confirmés à venir."""
        today = timezone.now().date()
        return cls.objects.filter(
            proposition__date__gte=today,
            statut=cls.Statut.CONFIRME
        ).order_by('proposition__date', 'proposition__heure')
    
    @classmethod
    def rdv_par_citoyen(cls, citoyen_id: int):
        """Retourne les rendez-vous d'un citoyen."""
        return cls.objects.filter(citoyen_id=citoyen_id).order_by('-proposition__date')
    
    @classmethod
    def statistiques_mensuelles(cls, mois: int = None, annee: int = None):
        """Statistiques des rendez-vous pour un mois."""
        from django.db.models import Count
        
        now = timezone.now()
        mois = mois or now.month
        annee = annee or now.year
        
        return cls.objects.filter(
            proposition__date__month=mois,
            proposition__date__year=annee
        ).values('statut').annotate(total=Count('id'))
