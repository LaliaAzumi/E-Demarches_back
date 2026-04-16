"""
================================================================================
COUCHE PRESENTATION (Presentation Layer)
================================================================================

Cette couche contient :
- Les vues API (Views/ViewSets)
- Les sérializers (adaptation DTO ↔ JSON)
- Les permissions (contrôle d'accès HTTP)
- Les filtres et pagination

PRINCIPE: Cette couche adapte les données pour le protocole HTTP/REST.
Elle ne contient PAS de logique métier, uniquement de la coordination.

PATTERN: Presentation Layer, Adapter Pattern
AGILE: Presentation = API Endpoints pour chaque User Story
================================================================================
"""

from .permissions import (
    IsCitoyen,
    IsAgent,
    IsAdministrateur,
    IsOwnerOrAdmin,
    CanAccessDemande,
)

from .serializers import (
    UtilisateurSerializer,
    DemandeSerializer,
    DocumentSerializer,
    NotificationSerializer,
    ServiceSerializer,
)

from .viewsets import (
    AuthViewSet,
    UtilisateurViewSet,
    DemandeViewSet,
    DocumentViewSet,
    NotificationViewSet,
    ServiceViewSet,
    RendezVousViewSet,
)

__all__ = [
    # Permissions
    'IsCitoyen',
    'IsAgent',
    'IsAdministrateur',
    'IsOwnerOrAdmin',
    'CanAccessDemande',
    # Serializers
    'UtilisateurSerializer',
    'DemandeSerializer',
    'DocumentSerializer',
    'NotificationSerializer',
    'ServiceSerializer',
    # ViewSets
    'AuthViewSet',
    'UtilisateurViewSet',
    'DemandeViewSet',
    'DocumentViewSet',
    'NotificationViewSet',
    'ServiceViewSet',
    'RendezVousViewSet',
]
