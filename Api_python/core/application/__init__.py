"""
================================================================================
COUCHE APPLICATION (Application Layer)
================================================================================

Cette couche contient :
- Les services métier (Use Cases)
- Les DTOs (Data Transfer Objects)
- Les workflows métiers
- La coordination entre Domain et Infrastructure

PRINCIPE: Cette couche orchestre les opérations sur les entités.
Elle contient la logique applicative, pas la logique métier.

PATTERN: Service Layer Pattern
AGILE: Services = User Story Implementation (Acceptance Criteria)
================================================================================
"""

from .services import (
    AuthService,
    DemandeService,
    NotificationService,
    RDVService,
    DocumentService,
)

from .dtos import (
    UserDTO,
    DemandeDTO,
    DocumentDTO,
    NotificationDTO,
)

__all__ = [
    # Services
    'AuthService',
    'DemandeService',
    'NotificationService',
    'RDVService',
    'DocumentService',
    # DTOs
    'UserDTO',
    'DemandeDTO',
    'DocumentDTO',
    'NotificationDTO',
]
