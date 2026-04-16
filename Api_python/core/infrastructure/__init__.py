"""
================================================================================
COUCHE INFRASTRUCTURE (Infrastructure Layer)
================================================================================

Cette couche contient :
- Les repositories (accès aux données)
- Les services externes (email, OAuth, paiement)
- Les adaptateurs de persistance (Django ORM)
- Les configurations techniques

PRINCIPE: Cette couche dépend de la couche Domain.
Elle implémente les interfaces définies dans le Domain.

PATTERN: Repository Pattern - Abstraction de la persistance
AGILE: Technical Tasks → Infrastructure Implementation
================================================================================
"""

from .repositories import (
    BaseRepository,
    UtilisateurRepository,
    DemandeRepository,
    DocumentRepository,
    NotificationRepository,
)

from .external_services import (
    EmailServiceInterface,
    OAuthServiceInterface,
    FileStorageInterface,
)

__all__ = [
    # Repositories
    'BaseRepository',
    'UtilisateurRepository',
    'DemandeRepository',
    'DocumentRepository',
    'NotificationRepository',
    # External Services
    'EmailServiceInterface',
    'OAuthServiceInterface',
    'FileStorageInterface',
]
