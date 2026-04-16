"""
================================================================================
MODULE: repositories.py
COUCHE: Infrastructure
RÔLE: Pattern Repository - Abstraction de l'accès aux données

ARCHITECTURE:
    BaseRepository (Abstract)
        ├── UtilisateurRepository
        ├── DemandeRepository
        ├── DocumentRepository
        └── NotificationRepository

PRINCIPE: Séparation entre logique métier et persistance.
Le Domain ne sait pas COMMENT les données sont stockées.

PATTERNS:
    - Repository Pattern
    - Unit of Work (transaction management)
    - Specification Pattern (critères de recherche)

AGILE: Repositories encapsulent les Technical Stories de persistance
================================================================================
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic, Dict, Any
from datetime import datetime

from ..domain.entities import (
    Utilisateur, CitoyenProfile, AgentProfile,
    Demande, Document, Traitement,
    RendezVous, Service, Notification, FAQEntry
)
from ..domain.value_objects import Email, Status, Role
from ..domain.exceptions import NotFoundException


# ============================================================================
# TYPE GENERIQUE
# ============================================================================

T = TypeVar('T')


# ============================================================================
# REPOSITORY ABSTRAIT (INTERFACE)
# ============================================================================

class BaseRepository(ABC, Generic[T]):
    """
    Classe abstraite définissant le contrat des repositories.
    
    Tous les repositories spécifiques doivent implémenter ces méthodes.
    
    TYPE GENERIQUE:
        T: Le type d'entité gérée par ce repository
    
    EXEMPLE:
        >>> class UtilisateurRepository(BaseRepository[Utilisateur]):
        ...     def find_by_id(self, id: int) -> Optional[Utilisateur]:
        ...         # Implémentation Django ORM
        ...         pass
    """
    
    @abstractmethod
    def find_by_id(self, entity_id: int) -> Optional[T]:
        """
        Recherche une entité par son ID.
        
        PARAMÈTRES:
            entity_id: Identifiant unique de l'entité
            
        RETOURNE:
            L'entité trouvée, ou None si inexistante
        """
        pass
    
    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Récupère toutes les entités avec pagination.
        
        PARAMÈTRES:
            limit: Nombre maximum d'entités à retourner
            offset: Décalage pour la pagination
            
        RETOURNE:
            Liste des entités
        """
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Sauvegarde une entité (création ou mise à jour).
        
        PARAMÈTRES:
            entity: Entité à sauvegarder
            
        RETOURNE:
            L'entité sauvegardée (avec ID généré si création)
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """
        Supprime une entité.
        
        PARAMÈTRES:
            entity_id: ID de l'entité à supprimer
            
        RETOURNE:
            True si supprimée, False sinon
        """
        pass
    
    @abstractmethod
    def count(self, filters: Optional[Dict] = None) -> int:
        """
        Compte les entités avec filtres optionnels.
        
        PARAMÈTRES:
            filters: Critères de filtrage
            
        RETOURNE:
            Nombre d'entités correspondantes
        """
        pass


# ============================================================================
# SPECIFICATIONS (CRITÈRES DE RECHERCHE)
# ============================================================================

class Specification(ABC):
    """
    Pattern Specification pour encapsuler les critères de recherche.
    
    Permet de composer des critères complexes de manière fluide.
    
    EXEMPLE:
        >>> spec = AndSpecification(
        ...     RoleSpecification(Role.AGENT),
        ...     ActiveSpecification()
        ... )
    """
    
    @abstractmethod
    def to_query(self) -> Dict[str, Any]:
        """Convertit la spécification en critères de requête."""
        pass
    
    def __and__(self, other: 'Specification') -> 'AndSpecification':
        """Opérateur AND pour combiner les spécifications."""
        return AndSpecification(self, other)
    
    def __or__(self, other: 'Specification') -> 'OrSpecification':
        """Opérateur OR pour combiner les spécifications."""
        return OrSpecification(self, other)


class AndSpecification(Specification):
    """Combinaison AND de deux spécifications."""
    
    def __init__(self, spec1: Specification, spec2: Specification):
        self.spec1 = spec1
        self.spec2 = spec2
    
    def to_query(self) -> Dict[str, Any]:
        """Fusionne les critères des deux spécifications."""
        query = {}
        query.update(self.spec1.to_query())
        query.update(self.spec2.to_query())
        return query


class OrSpecification(Specification):
    """Combinaison OR de deux spécifications."""
    
    def __init__(self, spec1: Specification, spec2: Specification):
        self.spec1 = spec1
        self.spec2 = spec2
    
    def to_query(self) -> Dict[str, Any]:
        """Crée une requête OR."""
        return {
            '__or': [
                self.spec1.to_query(),
                self.spec2.to_query()
            ]
        }


class RoleSpecification(Specification):
    """Filtre par rôle utilisateur."""
    
    def __init__(self, role: Role):
        self.role = role
    
    def to_query(self) -> Dict[str, Any]:
        return {'role': self.role.value}


class ActiveSpecification(Specification):
    """Filtre les entités actives uniquement."""
    
    def to_query(self) -> Dict[str, Any]:
        return {'is_active': True, 'is_deleted': False}


class StatusSpecification(Specification):
    """Filtre par statut."""
    
    def __init__(self, status: str):
        self.status = status
    
    def to_query(self) -> Dict[str, Any]:
        return {'status': self.status}


class DateRangeSpecification(Specification):
    """Filtre par plage de dates."""
    
    def __init__(self, field: str, start: datetime, end: datetime):
        self.field = field
        self.start = start
        self.end = end
    
    def to_query(self) -> Dict[str, Any]:
        return {
            f'{self.field}__gte': self.start,
            f'{self.field}__lte': self.end
        }


# ============================================================================
# REPOSITORY UTILISATEUR
# ============================================================================

class UtilisateurRepository(BaseRepository[Utilisateur]):
    """
    Repository pour la gestion des utilisateurs.
    
    RESPONSABILITÉS:
        - CRUD utilisateurs
        - Recherche par email
        - Gestion des profils associés
        - Authentification
    
    EXEMPLE:
        >>> repo = UtilisateurRepository()
        >>> user = repo.find_by_email(Email("test@example.com"))
        >>> users = repo.find_by_specification(
        ...     RoleSpecification(Role.AGENT) & ActiveSpecification()
        ... )
    """
    
    def find_by_email(self, email: Email) -> Optional[Utilisateur]:
        """
        Recherche un utilisateur par email.
        
        PARAMÈTRES:
            email: Email à rechercher
            
        RETOURNE:
            Utilisateur trouvé ou None
        """
        from ..models import Utilisateur as UtilisateurModel
        try:
            user = UtilisateurModel.objects.get(email=str(email))
            return self._to_entity(user)
        except UtilisateurModel.DoesNotExist:
            return None
    
    def find_by_social_id(self, provider: str, social_id: str) -> Optional[Utilisateur]:
        """
        Recherche un utilisateur par ID social OAuth.
        
        PARAMÈTRES:
            provider: Provider OAuth ('google', 'facebook')
            social_id: ID externe du provider
        """
        pass
    
    def find_by_specification(self, spec: Specification, 
                            limit: int = 100, offset: int = 0) -> List[Utilisateur]:
        """
        Recherche par spécification complexe.
        
        PARAMÈTRES:
            spec: Spécification de filtrage
            limit: Pagination - taille
            offset: Pagination - décalage
            
        RETOURNE:
            Liste des utilisateurs correspondants
        """
        pass
    
    def email_exists(self, email: Email, exclude_id: Optional[int] = None) -> bool:
        """
        Vérifie si un email existe déjà.
        
        PARAMÈTRES:
            email: Email à vérifier
            exclude_id: ID à exclure (pour les mises à jour)
            
        RETOURNE:
            True si l'email existe déjà
        """
        from ..models import Utilisateur as UtilisateurModel
        queryset = UtilisateurModel.objects.filter(email=str(email))
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()
    
    def authenticate(self, email: Email, password: str) -> Optional[Utilisateur]:
        """
        Authentifie un utilisateur.
        
        PARAMÈTRES:
            email: Email de connexion
            password: Mot de passe
            
        RETOURNE:
            Utilisateur authentifié ou None
        """
        from ..models import Utilisateur as UtilisateurModel
        from django.contrib.auth.hashers import check_password
        try:
            user = UtilisateurModel.objects.get(email=str(email))
            if check_password(password, user.password):
                return self._to_entity(user)
            return None
        except UtilisateurModel.DoesNotExist:
            return None
    
    def update_last_login(self, user_id: int) -> None:
        """Met à jour la date de dernière connexion."""
        pass
    
    # Profils
    def get_citoyen_profile(self, user_id: int) -> Optional[CitoyenProfile]:
        """Récupère le profil citoyen associé."""
        pass
    
    def get_agent_profile(self, user_id: int) -> Optional[AgentProfile]:
        """Récupère le profil agent associé."""
        pass
    
    def save_citoyen_profile(self, profile: CitoyenProfile) -> CitoyenProfile:
        """Sauvegarde un profil citoyen."""
        pass
    
    def save_agent_profile(self, profile: AgentProfile) -> AgentProfile:
        """Sauvegarde un profil agent."""
        pass


# ============================================================================
# REPOSITORY DEMANDE
# ============================================================================

class DemandeRepository(BaseRepository[Demande]):
    """
    Repository pour la gestion des demandes administratives.
    
    RESPONSABILITÉS:
        - CRUD demandes
        - Filtrage par statut, citoyen, agent, service
        - Statistiques et reporting
        - Gestion du workflow
    
    EXEMPLE:
        >>> repo = DemandeRepository()
        >>> demandes = repo.find_by_citoyen(citoyen_id=123)
        >>> stats = repo.get_statistics_by_status()
    """
    
    def find_by_citoyen(self, citoyen_id: int, 
                       limit: int = 100, offset: int = 0) -> List[Demande]:
        """
        Récupère les demandes d'un citoyen.
        
        PARAMÈTRES:
            citoyen_id: ID du citoyen
            limit, offset: Pagination
        """
        pass
    
    def find_by_agent(self, agent_id: int,
                     status: Optional[str] = None) -> List[Demande]:
        """
        Récupère les demandes assignées à un agent.
        
        PARAMÈTRES:
            agent_id: ID de l'agent
            status: Filtrer par statut optionnel
        """
        pass
    
    def find_by_service(self, service_id: int,
                       status: Optional[str] = None) -> List[Demande]:
        """Récupère les demandes par service."""
        pass
    
    def find_by_reference(self, reference: str) -> Optional[Demande]:
        """
        Recherche une demande par sa référence.
        
        EXEMPLE: DEM-2024-000123
        """
        pass
    
    def find_by_specification(self, spec: Specification,
                             limit: int = 100, offset: int = 0) -> List[Demande]:
        """Recherche avec spécification complexe."""
        pass
    
    def assign_to_agent(self, demande_id: int, agent_id: int) -> Demande:
        """
        Assigne une demande à un agent.
        
        LÈVE:
            NotFoundException: Si demande ou agent non trouvé
        """
        pass
    
    def change_status(self, demande_id: int, new_status: str,
                     changed_by_id: int, reason: Optional[str] = None) -> Demande:
        """
        Change le statut d'une demande avec traçabilité.
        
        LÈVE:
            NotFoundException: Si demande non trouvée
            BusinessRuleException: Si transition interdite
        """
        pass
    
    def get_overdue_demandes(self) -> List[Demande]:
        """Récupère les demandes en retard (dépassement SLA)."""
        pass
    
    def get_statistics_by_status(self) -> Dict[str, int]:
        """
        Retourne les statistiques par statut.
        
        RETOURNE:
            Dict: {'soumise': 45, 'en_traitement': 30, ...}
        """
        pass
    
    def generate_reference(self, demande: Demande) -> str:
        """
        Génère une référence unique pour une demande.
        
        FORMAT: DEM-YYYY-XXXXXX
        """
        pass
    
    def search(self, query: str, limit: int = 20) -> List[Demande]:
        """
        Recherche textuelle dans les demandes.
        
        PARAMÈTRES:
            query: Terme de recherche
            limit: Nombre de résultats max
        """
        pass


# ============================================================================
# REPOSITORY DOCUMENT
# ============================================================================

class DocumentRepository(BaseRepository[Document]):
    """
    Repository pour la gestion des documents.
    
    RESPONSABILITÉS:
        - CRUD documents
        - Association aux demandes
        - Gestion des types
    """
    
    def find_by_demande(self, demande_id: int) -> List[Document]:
        """Récupère tous les documents d'une demande."""
        pass
    
    def find_by_type(self, type_document: str, 
                    demande_id: Optional[int] = None) -> List[Document]:
        """Recherche par type de document."""
        pass
    
    def mark_as_verified(self, document_id: int, 
                        verified_by_id: int) -> Document:
        """Marque un document comme vérifié."""
        pass
    
    def get_total_size_by_demande(self, demande_id: int) -> int:
        """Calcule la taille totale des documents d'une demande."""
        pass


# ============================================================================
# REPOSITORY NOTIFICATION
# ============================================================================

class NotificationRepository(BaseRepository[Notification]):
    """
    Repository pour la gestion des notifications.
    
    RESPONSABILITÉS:
        - CRUD notifications
        - Marquage comme lu/non lu
        - Comptage des non lues
    """
    
    def find_by_destinataire(self, destinataire_id: int,
                            unread_only: bool = False,
                            limit: int = 50) -> List[Notification]:
        """
        Récupère les notifications d'un utilisateur.
        
        PARAMÈTRES:
            destinataire_id: ID de l'utilisateur
            unread_only: Ne retourner que les non lues
            limit: Limite de résultats
        """
        pass
    
    def count_unread(self, destinataire_id: int) -> int:
        """Compte les notifications non lues."""
        pass
    
    def mark_all_as_read(self, destinataire_id: int) -> int:
        """
        Marque toutes les notifications comme lues.
        
        RETOURNE:
            Nombre de notifications mises à jour
        """
        pass
    
    def find_by_demande(self, demande_id: int) -> List[Notification]:
        """Récupère les notifications liées à une demande."""
        pass
    
    def create_notification(self, destinataire_id: int, titre: str,
                          message: str, type_notif: str,
                          demande_id: Optional[int] = None,
                          lien_action: Optional[str] = None) -> Notification:
        """Crée une nouvelle notification."""
        pass


# ============================================================================
# UNIT OF WORK (GESTION DES TRANSACTIONS)
# ============================================================================

class UnitOfWork(ABC):
    """
    Pattern Unit of Work pour gérer les transactions.
    
    Garantit l'atomicité des opérations sur plusieurs repositories.
    
    EXEMPLE:
        >>> with UnitOfWork() as uow:
        ...     uow.utilisateurs.save(user)
        ...     uow.demandes.save(demande)
        ...     uow.commit()  # Tout ou rien
    """
    
    def __init__(self):
        self.utilisateurs: UtilisateurRepository = self._create_utilisateur_repo()
        self.demandes: DemandeRepository = self._create_demande_repo()
        self.documents: DocumentRepository = self._create_document_repo()
        self.notifications: NotificationRepository = self._create_notification_repo()
    
    @abstractmethod
    def _create_utilisateur_repo(self) -> UtilisateurRepository:
        pass
    
    @abstractmethod
    def _create_demande_repo(self) -> DemandeRepository:
        pass
    
    @abstractmethod
    def _create_document_repo(self) -> DocumentRepository:
        pass
    
    @abstractmethod
    def _create_notification_repo(self) -> NotificationRepository:
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Valide toutes les modifications."""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Annule toutes les modifications."""
        pass
    
    def __enter__(self):
        """Context manager - entrée."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - sortie avec gestion transaction."""
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
