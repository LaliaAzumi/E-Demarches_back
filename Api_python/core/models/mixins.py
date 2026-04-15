"""
Mixins abstraits pour les modèles.
"""

from django.db import models
from django.utils import timezone


class TimestampMixin(models.Model):
    """
    Mixin abstrait pour ajouter des timestamps automatiques.
    
    Attributs:
        created_at: Date/heure de création
        updated_at: Date/heure de dernière modification
    """
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        abstract = True


class ProfilMixin(models.Model):
    """
    Mixin abstrait pour les profils liés à un utilisateur.
    
    Attributs:
        utilisateur: Relation OneToOne vers Utilisateur
    """
    utilisateur = models.OneToOneField(
        'core.Utilisateur',
        on_delete=models.CASCADE,
        related_name='%(class)s_profile'
    )

    class Meta:
        abstract = True
    
    @property
    def email(self) -> str:
        """Retourne l'email de l'utilisateur."""
        return self.utilisateur.email
    
    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet formaté."""
        return self.utilisateur.nom_complet
    
    @property
    def nom(self) -> str:
        """Retourne le nom de famille."""
        return self.utilisateur.nom
    
    @property
    def prenom(self) -> str:
        """Retourne le prénom."""
        return self.utilisateur.prenom
    
    @property
    def telephone(self) -> str:
        """Retourne le numéro de téléphone."""
        return self.utilisateur.telephone
    
    @property
    def role(self) -> str:
        """Retourne le rôle de l'utilisateur."""
        return self.utilisateur.role


class StatutMixin(models.Model):
    """
    Mixin pour les modèles avec gestion de statut.
    
    À utiliser avec une classe définissant `class Statut`.
    """
    statut = models.CharField(max_length=20)
    
    class Meta:
        abstract = True
    
    @property
    def est_en_attente(self) -> bool:
        """Vérifie si le statut est 'en_attente'."""
        return self.statut == getattr(self.Statut, 'EN_ATTENTE', 'en_attente')
    
    @property
    def est_en_cours(self) -> bool:
        """Vérifie si le statut est 'en_cours'."""
        return self.statut == getattr(self.Statut, 'EN_COURS', 'en_cours')
    
    @property
    def est_validee(self) -> bool:
        """Vérifie si le statut est 'validee'."""
        return self.statut == getattr(self.Statut, 'VALIDEE', 'validee')
    
    @property
    def est_rejetee(self) -> bool:
        """Vérifie si le statut est 'rejetee'."""
        return self.statut == getattr(self.Statut, 'REJETEE', 'rejetee')
    
    @property
    def est_terminee(self) -> bool:
        """Vérifie si la demande est terminée (validée ou rejetée)."""
        return self.est_validee or self.est_rejetee
