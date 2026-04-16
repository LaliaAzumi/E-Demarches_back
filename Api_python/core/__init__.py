"""
================================================================================
PACKAGE: core
APPLICATION DJANGO: Plateforme Administrative

ARCHITECTURE LAYERED (MVC AVANCÉ):
    Ce package implémente une architecture en couches suivant les principes
    du Domain-Driven Design (DDD) et du pattern MVC.

    COUCHES:
        1. DOMAIN (Domain Layer)
           - Entities: Modèles métier purs
           - Value Objects: Objets de valeur immuables
           - Exceptions: Exceptions métier
           - Mixins: Fonctionnalités transversales

        2. INFRASTRUCTURE (Infrastructure Layer)
           - Repositories: Persistance des entités
           - External Services: Email, OAuth, Stockage

        3. APPLICATION (Application Layer)
           - Services: Cas d'utilisation (Use Cases)
           - DTOs: Objets de transfert de données

        4. PRESENTATION (Presentation Layer)
           - ViewSets: Endpoints API REST
           - Serializers: Adaptation JSON
           - Permissions: Contrôle d'accès

    MODÈLES DJANGO (ORM):
        - Utilisateur (Custom User)
        - Citoyen, Agent, Administrateur (Profils)
        - Service, Demande, Document, Traitement
        - RendezVous, Notification, FAQ

AGILE: Chaque couche correspond à un niveau d'abstraction métier
================================================================================
"""

# Version de l'application
__version__ = '1.0.0'

# Export des éléments principaux pour import simplifié
from .domain.exceptions import (
    DomainException,
    ValidationException,
    NotFoundException,
    PermissionDeniedException,
    AuthenticationException,
    BusinessRuleException,
)

from .domain.value_objects import (
    Email,
    PhoneNumber,
    Role,
)

__all__ = [
    'DomainException',
    'ValidationException',
    'NotFoundException',
    'PermissionDeniedException',
    'AuthenticationException',
    'BusinessRuleException',
    'Email',
    'PhoneNumber',
    'Role',
]
