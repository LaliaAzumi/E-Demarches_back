"""
================================================================================
COUCHE DOMAIN (Domain Layer)
================================================================================

Cette couche contient :
- Les entités métier (modèles de domaine)
- Les objets de valeur (Value Objects)
- Les exceptions métier
- Les interfaces des repositories (contrats)

PRINCIPE: Cette couche ne dépend d'aucune autre couche.
Elle représente le cœur métier de l'application.

Agile: User Stories → Domain Entities → Business Rules
================================================================================
"""

from .exceptions import (
    DomainException,
    ValidationException,
    NotFoundException,
    PermissionDeniedException,
    BusinessRuleException,
    AuthenticationException,
)

from .value_objects import (
    Email,
    PhoneNumber,
    Address,
    Status,
    Role,
    DateRange,
)

__all__ = [
    # Exceptions
    'DomainException',
    'ValidationException',
    'NotFoundException',
    'PermissionDeniedException',
    'BusinessRuleException',
    'AuthenticationException',
    # Value Objects
    'Email',
    'PhoneNumber',
    'Address',
    'Status',
    'Role',
    'DateRange',
]
