"""
Modèles pour les documents et traitements.
"""

import os
from datetime import datetime

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from .mixins import TimestampMixin
from .exceptions import DocumentException, ValidationException


class Document(TimestampMixin):
    """
    Document associé à une demande administrative.
    
    Attributs:
        id_document: Identifiant unique
        demande: Demande associée
        nom_document: Nom du fichier
        type_document: Type (PDF, Image, etc.)
        fichier: Fichier uploadé
        url: URL externe optionnelle
        date_upload: Date d'upload
    """
    
    class Type(models.TextChoices):
        PDF = 'pdf', 'PDF'
        IMAGE = 'image', 'Image'
        DOC = 'doc', 'Document Word'
        AUTRE = 'autre', 'Autre'
    
    # Taille max en MB
    TAILLE_MAX_MB = 10
    
    id = models.AutoField(primary_key=True)
    id_document = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True,
        verbose_name="ID du document"
    )
    demande = models.ForeignKey(
        'core.DemandeAdministrative',
        on_delete=models.CASCADE, 
        related_name='documents',
        verbose_name="Demande"
    )
    nom_document = models.CharField(
        max_length=255,
        verbose_name="Nom du document"
    )
    type_document = models.CharField(
        max_length=50, 
        choices=Type.choices, 
        default=Type.AUTRE,
        verbose_name="Type"
    )
    fichier = models.FileField(
        upload_to='documents/%Y/%m/',
        null=True, 
        blank=True,
        verbose_name="Fichier"
    )
    url = models.URLField(
        null=True, 
        blank=True,
        verbose_name="URL externe"
    )
    date_upload = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date d'upload"
    )

    class Meta:
        db_table = 'documents'
        ordering = ['-date_upload']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'

    def __str__(self) -> str:
        return self.nom_document
    
    def __repr__(self) -> str:
        return f"<Document: {self.nom_document} - {self.type_document}>"
    
    # ========== Validation et sauvegarde ==========
    
    def clean(self):
        """Validation avant sauvegarde."""
        super().clean()
        
        # Vérifier qu'il y a soit un fichier, soit une URL
        if not self.fichier and not self.url:
            raise ValidationException(
                "Un fichier ou une URL doit être fourni",
                field='fichier'
            )
        
        # Vérifier la taille du fichier
        if self.fichier:
            taille_mb = self.fichier.size / (1024 * 1024)
            if taille_mb > self.TAILLE_MAX_MB:
                raise DocumentException(
                    f"Fichier trop gros ({taille_mb:.1f}MB). Maximum: {self.TAILLE_MAX_MB}MB",
                    DocumentException.FICHIER_TROP_GROS,
                    self.nom_document
                )
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec génération d'ID et détection de type."""
        if not self.id_document:
            self.id_document = f"DOC-{self.demande.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Détecter le type à partir de l'extension
        if self.fichier and self.type_document == self.Type.AUTRE:
            self.type_document = self._detecter_type()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def _detecter_type(self) -> str:
        """Détecte le type de document à partir de l'extension."""
        if not self.fichier:
            return self.Type.AUTRE
        
        ext = os.path.splitext(self.fichier.name)[1].lower()
        
        extensions = {
            '.pdf': self.Type.PDF,
            '.jpg': self.Type.IMAGE,
            '.jpeg': self.Type.IMAGE,
            '.png': self.Type.IMAGE,
            '.gif': self.Type.IMAGE,
            '.doc': self.Type.DOC,
            '.docx': self.Type.DOC,
        }
        
        return extensions.get(ext, self.Type.AUTRE)
    
    # ========== Propriétés ==========
    
    @property
    def taille_fichier(self) -> int:
        """Retourne la taille du fichier en octets."""
        if self.fichier and os.path.exists(self.fichier.path):
            return os.path.getsize(self.fichier.path)
        return 0
    
    @property
    def taille_fichier_affichage(self) -> str:
        """Retourne la taille formatée (KB, MB)."""
        taille = self.taille_fichier
        if taille == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if taille < 1024:
                return f"{taille:.1f} {unit}"
            taille /= 1024
        return f"{taille:.1f} TB"
    
    @property
    def extension(self) -> str:
        """Retourne l'extension du fichier."""
        if self.fichier:
            return os.path.splitext(self.fichier.name)[1].lower()
        return ""
    
    # ========== Méthodes métier ==========
    
    def televerser(self, fichier):
        """
        Remplace le fichier existant.
        
        Args:
            fichier: Nouveau fichier
        """
        # Supprimer l'ancien fichier
        if self.fichier and os.path.isfile(self.fichier.path):
            os.remove(self.fichier.path)
        
        self.fichier = fichier
        self.nom_document = fichier.name
        self.type_document = self._detecter_type()
        self.save()
    
    def supprimer_fichier(self):
        """Supprime le fichier physique et l'entrée en base."""
        if self.fichier and os.path.isfile(self.fichier.path):
            os.remove(self.fichier.path)
        self.delete()
    
    def telecharger(self):
        """Retourne le fichier pour téléchargement."""
        if not self.fichier:
            raise DocumentException(
                "Aucun fichier disponible",
                DocumentException.DOCUMENT_INEXISTANT
            )
        return self.fichier
    
    def get_url(self) -> str:
        """Retourne l'URL d'accès au document."""
        if self.url:
            return self.url
        if self.fichier:
            return self.fichier.url
        return ""
    
    @classmethod
    def par_type(cls, type_doc: str):
        """Filtre les documents par type."""
        return cls.objects.filter(type_document=type_doc)
    
    @classmethod
    def statistiques_par_type(cls):
        """Statistiques des documents par type."""
        from django.db.models import Count
        return cls.objects.values('type_document').annotate(total=Count('id'))


class Traitement(TimestampMixin):
    """
    Traitement d'une demande par un agent.
    
    Attributs:
        demande: Demande traitée
        agent: Agent ayant effectué le traitement
        commentaire: Notes sur le traitement
        statut_apres_traitement: Statut résultant
        date_traitement: Date du traitement
    """
    
    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        EN_COURS = 'en_cours', 'En cours'
        VALIDEE = 'validee', 'Validée'
        REJETEE = 'rejetee', 'Rejetée'

    id = models.AutoField(primary_key=True)
    demande = models.ForeignKey(
        'core.DemandeAdministrative',
        on_delete=models.CASCADE, 
        related_name='traitements',
        verbose_name="Demande"
    )
    agent = models.ForeignKey(
        'core.AgentAdministratif',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='traitements',
        verbose_name="Agent"
    )
    commentaire = models.TextField(
        null=True, 
        blank=True,
        verbose_name="Commentaire"
    )
    statut_apres_traitement = models.CharField(
        max_length=20, 
        choices=Statut.choices, 
        null=True, 
        blank=True,
        verbose_name="Statut après traitement"
    )
    date_traitement = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date du traitement"
    )

    class Meta:
        db_table = 'traitements'
        ordering = ['-date_traitement']
        verbose_name = 'Traitement'
        verbose_name_plural = 'Traitements'

    def __str__(self) -> str:
        return f"Traitement #{self.id} - {self.demande.id_demande}"
    
    def __repr__(self) -> str:
        return f"<Traitement: {self.id} - Agent: {self.agent}>"
    
    # ========== Propriétés ==========
    
    @property
    def est_validation(self) -> bool:
        """Vérifie si c'est une validation."""
        return self.statut_apres_traitement == self.Statut.VALIDEE
    
    @property
    def est_rejet(self) -> bool:
        """Vérifie si c'est un rejet."""
        return self.statut_apres_traitement == self.Statut.REJETEE
    
    # ========== Méthodes de classe ==========
    
    @classmethod
    def derniers_traitements(cls, limite: int = 10):
        """Retourne les derniers traitements."""
        return cls.objects.all()[:limite]
    
    @classmethod
    def traitements_par_agent(cls, agent_id: int):
        """Retourne les traitements d'un agent spécifique."""
        return cls.objects.filter(agent_id=agent_id)
    
    @classmethod
    def statistiques_mensuelles(cls, mois: int = None, annee: int = None):
        """Statistiques des traitements pour un mois donné."""
        from django.db.models import Count, Q
        
        now = timezone.now()
        mois = mois or now.month
        annee = annee or now.year
        
        return cls.objects.filter(
            date_traitement__month=mois,
            date_traitement__year=annee
        ).values('statut_apres_traitement').annotate(
            total=Count('id'),
            agents_distincts=Count('agent', distinct=True)
        )
