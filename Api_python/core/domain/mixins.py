"""
================================================================================
MODULE: mixins.py
COUCHE: Domain
RÔLE: Mixins réutilisables pour les entités métier

ARCHITECTURE:
    Les mixins sont des classes abstraites fournissant des fonctionnalités
    transversales aux modèles métier sans imposer une hiérarchie stricte.

    TimestampMixin: Gestion des dates de création/modification
    SoftDeleteMixin: Suppression logique (non physique)
    StatusMixin: Gestion du statut avec historique
    AuditMixin: Traçabilité des modifications
    VersionMixin: Versionnement des entités

AGILE: Mixins = Fonctionnalités transversales partagées entre User Stories
================================================================================
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class TimestampMixin:
    """
    Mixin ajoutant les champs de gestion temporelle.
    
    FOURNIT:
        created_at (datetime): Date et heure de création
        updated_at (datetime): Date et heure de dernière modification
    
    EXEMPLE:
        >>> @dataclass
        ... class Demande(TimestampMixin):
        ...     titre: str
        ... 
        >>> d = Demande(titre="Test")
        >>> print(d.created_at)  # 2024-01-15 10:30:00
    """
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def touch(self) -> None:
        """
        Met à jour la date de modification.
        
        À appeler manuellement lors des modifications.
        """
        self.updated_at = datetime.now()
    
    @property
    def age_seconds(self) -> float:
        """Temps écoulé depuis la création en secondes."""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def age_minutes(self) -> float:
        """Temps écoulé depuis la création en minutes."""
        return self.age_seconds / 60
    
    @property
    def age_hours(self) -> float:
        """Temps écoulé depuis la création en heures."""
        return self.age_minutes / 60
    
    @property
    def age_days(self) -> float:
        """Temps écoulé depuis la création en jours."""
        return self.age_hours / 24


@dataclass
class SoftDeleteMixin:
    """
    Mixin permettant la suppression logique (soft delete).
    
    PRINCIPE: Au lieu de supprimer physiquement la donnée,
    on la marque comme supprimée avec une date.
    
    FOURNIT:
        is_deleted (bool): Indique si l'entité est supprimée
        deleted_at (Optional[datetime]): Date de suppression
        deleted_by (Optional[str]): Utilisateur ayant supprimé
    
    EXEMPLE:
        >>> entity.soft_delete(deleted_by="admin@example.com")
        >>> print(entity.is_deleted)  # True
        >>> entity.restore()
        >>> print(entity.is_deleted)  # False
    """
    
    is_deleted: bool = field(default=False)
    deleted_at: Optional[datetime] = field(default=None)
    deleted_by: Optional[str] = field(default=None)
    
    def soft_delete(self, deleted_by: Optional[str] = None) -> None:
        """
        Marque l'entité comme supprimée.
        
        PARAMÈTRES:
            deleted_by: Identifiant de l'utilisateur effectuant la suppression
        """
        self.is_deleted = True
        self.deleted_at = datetime.now()
        self.deleted_by = deleted_by
    
    def restore(self) -> None:
        """Restaure une entité précédemment supprimée."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
    
    @property
    def is_active(self) -> bool:
        """Vérifie si l'entité est active (non supprimée)."""
        return not self.is_deleted


@dataclass
class StatusMixin:
    """
    Mixin pour la gestion des statuts avec historique.
    
    FOURNIT:
        status (str): Statut actuel
        status_history (List[Dict]): Historique des changements
    
    EXEMPLE:
        >>> entity.change_status(
        ...     new_status="en_traitement",
        ...     changed_by="agent@example.com",
        ...     reason="Début du traitement"
        ... )
    """
    
    status: str = field(default="created")
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def change_status(
        self,
        new_status: str,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        """
        Change le statut avec traçabilité.
        
        PARAMÈTRES:
            new_status: Nouveau statut à appliquer
            changed_by: Identifiant de l'utilisateur modifiant
            reason: Raison du changement
        """
        old_status = self.status
        
        # Enregistrer dans l'historique
        self.status_history.append({
            'from': old_status,
            'to': new_status,
            'at': datetime.now().isoformat(),
            'by': changed_by,
            'reason': reason
        })
        
        # Mettre à jour le statut
        self.status = new_status
    
    def get_status_at(self, target_date: datetime) -> Optional[str]:
        """
        Récupère le statut à une date donnée.
        
        PARAMÈTRES:
            target_date: Date à laquelle récupérer le statut
            
        RETOURNE:
            Le statut à cette date, ou None si pas d'historique
        """
        for entry in reversed(self.status_history):
            entry_date = datetime.fromisoformat(entry['at'])
            if entry_date <= target_date:
                return entry['to']
        return self.status if self.status else None
    
    @property
    def last_status_change(self) -> Optional[Dict]:
        """Retourne le dernier changement de statut."""
        return self.status_history[-1] if self.status_history else None


@dataclass
class AuditMixin:
    """
    Mixin pour la traçabilité complète des modifications.
    
    FOURNIT:
        created_by (str): Créateur de l'entité
        updated_by (str): Dernier modificateur
        version (int): Numéro de version (optimistic locking)
    
    EXEMPLE:
        >>> entity.increment_version(updated_by="user@example.com")
    """
    
    created_by: Optional[str] = field(default=None)
    updated_by: Optional[str] = field(default=None)
    version: int = field(default=1)
    
    def increment_version(self, updated_by: str) -> None:
        """
        Incrémente la version et enregistre le modificateur.
        
        UTILISATION: Appeler à chaque modification significative.
        
        PARAMÈTRES:
            updated_by: Identifiant de l'utilisateur modifiant
        """
        self.version += 1
        self.updated_by = updated_by
    
    def check_version(self, expected_version: int) -> bool:
        """
        Vérifie la version (optimistic locking).
        
        RETOURNE:
            True si les versions correspondent, False sinon
        """
        return self.version == expected_version


class ValidatableMixin(ABC):
    """
    Mixin abstrait pour les entités validables.
    
    OBLIGATION: Les classes filles doivent implémenter validate().
    
    EXEMPLE:
        >>> @dataclass
        ... class Demande(ValidatableMixin):
        ...     titre: str
        ...     
        ...     def validate(self) -> List[str]:
        ...         errors = []
        ...         if not self.titre:
        ...             errors.append("Titre requis")
        ...         return errors
    """
    
    @abstractmethod
    def validate(self) -> List[str]:
        """
        Valide l'entité et retourne la liste des erreurs.
        
        RETOURNE:
            Liste des messages d'erreur (vide si valide)
        """
        pass
    
    def is_valid(self) -> bool:
        """Vérifie si l'entité est valide."""
        return len(self.validate()) == 0
    
    def validate_or_raise(self) -> None:
        """Lève une exception si l'entité est invalide."""
        errors = self.validate()
        if errors:
            from .exceptions import ValidationException
            raise ValidationException(
                message="Validation échouée",
                details={'errors': errors}
            )


@dataclass
class SearchableMixin:
    """
    Mixin pour les entités supportant la recherche textuelle.
    
    FOURNIT:
        search_text (str): Champs concaténés pour la recherche
        search_vector: Vector pour recherche full-text (PostgreSQL)
    
    EXEMPLE:
        >>> entity.update_search_text([entity.nom, entity.prenom, entity.email])
    """
    
    search_text: str = field(default="")
    
    def update_search_text(self, fields: List[str]) -> None:
        """
        Met à jour le texte de recherche.
        
        PARAMÈTRES:
            fields: Liste des champs à concaténer
        """
        self.search_text = " ".join(
            str(f).lower() for f in fields if f
        )
    
    def matches_search(self, query: str) -> bool:
        """Vérifie si l'entité correspond à la requête."""
        return query.lower() in self.search_text


# ============================================================================
# MIXINS SPÉCIFIQUES AU MÉTIER
# ============================================================================

@dataclass
class WorkflowMixin(StatusMixin):
    """
    Mixin spécialisé pour les entités avec workflow métier.
    
    FOURNIT:
        - Gestion des transitions autorisées
        - Validation des changements de statut
    
    EXEMPLE:
        >>> class Demande(WorkflowMixin):
        ...     ALLOWED_TRANSITIONS = {
        ...         'brouillon': ['soumise'],
        ...         'soumise': ['en_traitement', 'rejetee'],
        ...     }
    """
    
    # À définir dans la classe fille
    ALLOWED_TRANSITIONS: Dict[str, List[str]] = field(default_factory=dict)
    
    def can_transition_to(self, new_status: str) -> bool:
        """
        Vérifie si la transition est autorisée.
        
        RETOURNE:
            True si la transition est permise, False sinon
        """
        if not self.ALLOWED_TRANSITIONS:
            return True
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])
        return new_status in allowed
    
    def transition_to(
        self,
        new_status: str,
        changed_by: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        """
        Effectue une transition de statut validée.
        
        LÈVE:
            BusinessRuleException: Si la transition n'est pas autorisée
        """
        if not self.can_transition_to(new_status):
            from .exceptions import BusinessRuleException, ExceptionCode
            raise BusinessRuleException(
                message=f"Transition de '{self.status}' vers '{new_status}' interdite",
                rule_name='workflow_transition',
                code=ExceptionCode.DEMANDE_INVALID_STATUS,
                details={
                    'from_status': self.status,
                    'to_status': new_status,
                    'allowed_transitions': self.ALLOWED_TRANSITIONS.get(self.status, [])
                }
            )
        
        self.change_status(new_status, changed_by, reason)
