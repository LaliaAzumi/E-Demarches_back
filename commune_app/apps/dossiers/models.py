from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from apps.users.models import Citoyen, Agent


class Demande(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('validee', 'Validée'),
        ('rejetee', 'Rejetée'),
    ]

    id = models.AutoField(primary_key=True)
    citoyen = models.ForeignKey(
        Citoyen,
        on_delete=models.CASCADE,
        db_column='citoyen_id'
    )
    type_demande = models.CharField(max_length=100, db_column='type')
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        db_column='statut'
    )
    date_demande = models.DateTimeField(auto_now_add=True, db_column='date_demande')

    class Meta:
        db_table = 'demandes'
        ordering = ['-date_demande']
        verbose_name = 'Demande'
        verbose_name_plural = 'Demandes'
        indexes = [
            models.Index(fields=['citoyen', 'statut']),
            models.Index(fields=['date_demande']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"Demande #{self.id} - {self.type_demande} ({self.get_statut_display()})"


class Traitement(models.Model):
    id = models.AutoField(primary_key=True)
    demande = models.ForeignKey(
        Demande,
        on_delete=models.CASCADE,
        related_name='traitements',
        db_column='demande_id'
    )
    agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='agent_id'
    )
    commentaire = models.TextField(null=True, blank=True)
    statut_apres_traitement = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        db_column='statut_apres_traitement'
    )
    date_traitement = models.DateTimeField(auto_now_add=True, db_column='date_traitement')

    class Meta:
        db_table = 'traitements'
        ordering = ['-date_traitement']
        verbose_name = 'Traitement'
        verbose_name_plural = 'Traitements'
        indexes = [
            models.Index(fields=['demande']),
            models.Index(fields=['agent']),
            models.Index(fields=['date_traitement']),
        ]

    def __str__(self):
        return f"Traitement de la demande #{self.demande.id} par {self.agent}"


class PropositionRDV(models.Model):
    STATUT_CHOICES = [
        ('propose', 'Proposé'),
        ('choisi', 'Choisi'),
        ('refuse', 'Refusé'),
        ('expire', 'Expiré'),
    ]

    id = models.AutoField(primary_key=True)
    demande = models.ForeignKey(
        Demande,
        on_delete=models.CASCADE,
        related_name='propositions_rdv',
        db_column='demande_id'
    )
    agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='agent_id'
    )
    date = models.DateField()
    heure = models.TimeField()
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='propose',
        db_column='statut'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        db_table = 'propositions_rdv'
        verbose_name = 'Proposition de RDV'
        verbose_name_plural = 'Propositions de RDV'
        indexes = [
            models.Index(fields=['demande', 'statut']),
            models.Index(fields=['date']),
            models.Index(fields=['agent']),
        ]

    def clean(self):
        # Validation: la date du RDV doit être dans le futur
        if self.date and self.heure:
            rdv_datetime = datetime.combine(self.date, self.heure)
            if rdv_datetime < timezone.now():
                raise ValidationError("La date et l'heure du rendez-vous doivent être dans le futur.")

    def __str__(self):
        return f"RDV proposé le {self.date} à {self.heure}"


class RendezVous(models.Model):
    STATUT_CHOICES = [
        ('confirme', 'Confirmé'),
        ('annule', 'Annulé'),
        ('passe', 'Passé'),
    ]

    id = models.AutoField(primary_key=True)
    proposition = models.OneToOneField(
        PropositionRDV,
        on_delete=models.CASCADE,
        db_column='proposition_id'
    )
    citoyen = models.ForeignKey(
        Citoyen,
        on_delete=models.CASCADE,
        db_column='citoyen_id'
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='confirme',
        db_column='statut'
    )
    date_confirmation = models.DateTimeField(auto_now_add=True, db_column='date_confirmation')

    class Meta:
        db_table = 'rendez_vous'
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        indexes = [
            models.Index(fields=['citoyen']),
            models.Index(fields=['proposition']),
            models.Index(fields=['date_confirmation']),
        ]

    def __str__(self):
        return f"RDV confirmé le {self.proposition.date} à {self.proposition.heure}"
