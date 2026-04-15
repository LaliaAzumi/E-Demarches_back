"""
Modèles pour les demandes administratives et services.
"""

import random
import string
from datetime import datetime

from django.db import models
from django.utils import timezone
from django.db.models import Count
from django.core.exceptions import ValidationError

from .mixins import TimestampMixin, StatutMixin
from .exceptions import DemandeException, ValidationException


class ServiceAdministratif(TimestampMixin):
    """
    Service administratif disponible pour les demandes.
    
    Attributs:
        nom_service: Nom du service
        description: Description détaillée
        delai_traitement: Délai estimé en jours
        actif: Si le service est disponible
    """
    
    id = models.AutoField(primary_key=True)
    nom_service = models.CharField(max_length=100, verbose_name="Nom du service")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    delai_traitement = models.IntegerField(
        help_text="Délai en jours",
        null=True, 
        blank=True,
        verbose_name="Délai de traitement"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        db_table = 'services_administratifs'
        ordering = ['nom_service']
        verbose_name = 'Service administratif'
        verbose_name_plural = 'Services administratifs'

    def __str__(self) -> str:
        return self.nom_service
    
    def __repr__(self) -> str:
        return f"<Service: {self.nom_service}>"
    
    # ========== Propriétés ==========
    
    @property
    def nombre_demandes_actives(self) -> int:
        """Compte les demandes non terminées pour ce service."""
        return self.demandes.exclude(
            statut__in=['validee', 'rejetee']
        ).count()
    
    @property
    def nombre_demandes_total(self) -> int:
        """Compte toutes les demandes pour ce service."""
        return self.demandes.count()
    
    # ========== Méthodes métier ==========
    
    def desactiver(self):
        """Désactive le service (plus disponible pour nouvelles demandes)."""
        self.actif = False
        self.save(update_fields=['actif'])
    
    def reactiver(self):
        """Réactive le service."""
        self.actif = True
        self.save(update_fields=['actif'])
    
    @classmethod
    def services_actifs(cls):
        """Retourne les services actuellement actifs."""
        return cls.objects.filter(actif=True)
    
    @classmethod
    def statistiques_demandes(cls):
        """Statistiques des demandes par service."""
        return cls.objects.annotate(
            total_demandes=Count('demandes'),
            demandes_en_cours=Count('demandes', filter=~models.Q(
                demandes__statut__in=['validee', 'rejetee']
            ))
        )


class DemandeAdministrative(TimestampMixin, StatutMixin):
    """
    Demande administrative avec workflow complet.
    
    Attributs:
        id_demande: Identifiant unique généré
        citoyen: Citoyen demandeur
        service: Service concerné
        type_demande: Type de demande
        statut: Statut actuel de la demande
        motif_rejet: Raison du rejet (si applicable)
        date_demande: Date de création
    """
    
    class Type(models.TextChoices):
        CARTE_IDENTITE = 'carte_identite', 'Carte d\'identité'
        PASSEPORT = 'passeport', 'Passeport'
        ACTE_NAISSANCE = 'acte_naissance', 'Acte de naissance'
        ACTE_MARIAGE = 'acte_mariage', 'Acte de mariage'
        AUTRE = 'autre', 'Autre'

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        EN_COURS = 'en_cours', 'En cours'
        VALIDEE = 'validee', 'Validée'
        REJETEE = 'rejetee', 'Rejetée'

    id = models.AutoField(primary_key=True)
    id_demande = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True,
        verbose_name="ID de demande"
    )
    citoyen = models.ForeignKey(
        'core.Citoyen', 
        on_delete=models.CASCADE, 
        related_name='demandes',
        verbose_name="Citoyen"
    )
    service = models.ForeignKey(
        ServiceAdministratif,
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='demandes',
        verbose_name="Service"
    )
    type_demande = models.CharField(
        max_length=100, 
        choices=Type.choices,
        verbose_name="Type de demande"
    )
    statut = models.CharField(
        max_length=20, 
        choices=Statut.choices, 
        default=Statut.EN_ATTENTE,
        verbose_name="Statut"
    )
    motif_rejet = models.TextField(
        null=True, 
        blank=True,
        verbose_name="Motif du rejet"
    )
    date_demande = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de demande"
    )

    class Meta:
        db_table = 'demandes'
        ordering = ['-date_demande']
        verbose_name = 'Demande administrative'
        verbose_name_plural = 'Demandes administratives'

    def __str__(self) -> str:
        return f"Demande #{self.id_demande or self.id} - {self.get_type_demande_display()}"
    
    def __repr__(self) -> str:
        return f"<Demande: {self.id} - {self.citoyen.nom_complet}>"
    
    # ========== Sauvegarde et génération ID ==========
    
    def save(self, *args, **kwargs):
        """Génère l'ID unique avant la première sauvegarde."""
        if not self.id_demande:
            self.id_demande = self._generer_id()
        super().save(*args, **kwargs)
    
    def _generer_id(self) -> str:
        """Génère un ID unique formaté."""
        prefix = self.type_demande[:3].upper()
        suffix = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}-{suffix}"
    
    # ========== Méthodes de statut ==========
    
    def changer_statut(self, nouveau_statut: str, motif: str = None):
        """
        Change le statut avec validation et notification.
        
        Args:
            nouveau_statut: Le nouveau statut
            motif: Motif du changement (requis pour rejet)
            
        Raises:
            DemandeException: Si le statut est invalide ou transition impossible
        """
        # Vérifier que le statut est valide
        if nouveau_statut not in [s[0] for s in self.Statut.choices]:
            raise DemandeException(
                f"Statut invalide: {nouveau_statut}",
                DemandeException.STATUT_INVALIDE,
                self.id
            )
        
        # Vérifier les transitions valides
        transitions_valides = self._get_transitions_valides()
        if nouveau_statut not in transitions_valides.get(self.statut, []):
            raise DemandeException(
                f"Transition de '{self.statut}' vers '{nouveau_statut}' non autorisée",
                DemandeException.TRANSITION_INVALIDE,
                self.id
            )
        
        # Vérifier le motif pour un rejet
        if nouveau_statut == self.Statut.REJETEE and not motif:
            raise ValidationException(
                "Un motif de rejet est requis",
                field='motif_rejet'
            )
        
        ancien_statut = self.statut
        self.statut = nouveau_statut
        
        if nouveau_statut == self.Statut.REJETEE:
            self.motif_rejet = motif
        
        self.save()
        
        # Créer une notification pour le citoyen
        self._notifier_changement_statut(ancien_statut, nouveau_statut)
    
    def _get_transitions_valides(self):
        """Définit les transitions de statut autorisées."""
        return {
            self.Statut.EN_ATTENTE: [self.Statut.EN_COURS, self.Statut.REJETEE],
            self.Statut.EN_COURS: [self.Statut.VALIDEE, self.Statut.REJETEE],
            self.Statut.VALIDEE: [],  # Statut final
            self.Statut.REJETEE: [],  # Statut final
        }
    
    def _notifier_changement_statut(self, ancien: str, nouveau: str):
        """Crée une notification de changement de statut."""
        from .notifications import Notification
        
        messages = {
            self.Statut.EN_COURS: f"Votre demande {self.id_demande} est maintenant en cours de traitement.",
            self.Statut.VALIDEE: f"Votre demande {self.id_demande} a été validée avec succès !",
            self.Statut.REJETEE: f"Votre demande {self.id_demande} a été rejetée. Motif: {self.motif_rejet}",
        }
        
        message = messages.get(nouveau, 
            f"Le statut de votre demande {self.id_demande} est passé de '{ancien}' à '{nouveau}'")
        
        Notification.objects.create(
            utilisateur=self.citoyen.utilisateur,
            type_notification=Notification.Type.CHANGEMENT_STATUT,
            message=message
        )
    
    # ========== Méthodes de documents ==========
    
    def ajouter_document(self, fichier, nom: str = None, type_doc: str = None):
        """
        Ajoute un document à la demande.
        
        Args:
            fichier: Fichier à uploader
            nom: Nom du document
            type_doc: Type de document
            
        Returns:
            Document: Le document créé
        """
        from .documents import Document
        
        return Document.objects.create(
            demande=self,
            fichier=fichier,
            nom_document=nom or fichier.name,
            type_document=type_doc or Document.Type.AUTRE
        )
    
    def obtenir_documents(self):
        """Retourne tous les documents associés."""
        return self.documents.all()
    
    def nombre_documents(self) -> int:
        """Compte les documents associés."""
        return self.documents.count()
    
    # ========== Méthodes de rendez-vous ==========
    
    def propositions_rdv_actives(self):
        """Retourne les propositions de RDV non expirées."""
        return self.propositions_rdv.filter(
            statut='propose',
            date__gte=timezone.now().date()
        )
    
    def a_propositions_rdv(self) -> bool:
        """Vérifie s'il y a des propositions de RDV actives."""
        return self.propositions_rdv_actives().exists()
    
    # ========== Méthodes de classe ==========
    
    @classmethod
    def statistiques_par_statut(cls):
        """Statistiques des demandes groupées par statut."""
        return cls.objects.values('statut').annotate(total=Count('id'))
    
    @classmethod
    def statistiques_par_type(cls):
        """Statistiques des demandes groupées par type."""
        return cls.objects.values('type_demande').annotate(total=Count('id'))
    
    @classmethod
    def demandes_en_retard(cls):
        """Demandes qui pourraient être en retard (optionnel)."""
        # À implémenter selon les règles métier
        pass
