"""
================================================================================
FICHIER: urls.py (Application)
APPLICATION: core
RÔLE: Routage URL de l'application core

ARCHITECTURE:
    Définit toutes les routes API spécifiques à l'application.
    Utilise DefaultRouter de DRF pour générer automatiquement les URLs.

    ORGANISATION:
        1. Enregistrement des ViewSets dans le router
        2. Routes personnalisées (non-CRUD)
        3. Inclusion dans urlpatterns

    CONVENTION:
        - Routes CRUD générées automatiquement
        - Routes d'action sous /{resource}/{id}/{action}/

AGILE: URLs = API Endpoints pour chaque User Story
================================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import des ViewSets
from .presentation.viewsets import (
    AuthViewSet,
    UtilisateurViewSet,
    DemandeViewSet,
    DocumentViewSet,
    NotificationViewSet,
    ServiceViewSet,
    RendezVousViewSet,
)

# Import des vues fonctionnelles si nécessaire
# from .presentation.views import some_function_view


# =============================================================================
# CONFIGURATION DU ROUTER
# =============================================================================

# Création du router DRF
# Le DefaultRouter génère automatiquement les URLs CRUD
router = DefaultRouter()

# Enregistrement des ViewSets
# Format: router.register(r'route', ViewSet, basename='nom')

# Authentification
router.register(r'auth', AuthViewSet, basename='auth')

# Utilisateurs
router.register(r'utilisateurs', UtilisateurViewSet, basename='utilisateur')

# Demandes administratives
router.register(r'demandes', DemandeViewSet, basename='demande')

# Documents
router.register(r'documents', DocumentViewSet, basename='document')

# Notifications
router.register(r'notifications', NotificationViewSet, basename='notification')

# Services
router.register(r'services', ServiceViewSet, basename='service')

# Rendez-vous
router.register(r'rendez-vous', RendezVousViewSet, basename='rendez-vous')


# =============================================================================
# URLS PERSONNALISÉES (HORS ROUTER)
# =============================================================================

# Routes qui ne rentrent pas dans le pattern CRUD standard
# Par exemple: /api/health/, /api/status/, etc.

custom_urls = [
    # Exemple: endpoint de santé
    # path('health/', HealthCheckView.as_view(), name='health-check'),
    
    # Exemple: endpoint de statistiques globales
    # path('stats/', GlobalStatsView.as_view(), name='global-stats'),
]


# =============================================================================
# ASSEMBLAGE DES URLS
# =============================================================================

urlpatterns = [
    # Inclusion des routes générées par le router
    # Ces routes incluent toutes les URLs CRUD des ViewSets
    path('', include(router.urls)),
    
    # Routes personnalisées
    # path('custom/', include(custom_urls)),
]


# =============================================================================
# DOCUMENTATION DES ROUTES GÉNÉRÉES
# =============================================================================

"""
ROUTES CRUD AUTOMATIQUEMENT GÉNÉRÉES:

Pour chaque ViewSet enregistré, le DefaultRouter crée:

UtilisateurViewSet:
    GET    /api/utilisateurs/              → list()
    POST   /api/utilisateurs/              → create()
    GET    /api/utilisateurs/{id}/         → retrieve()
    PUT    /api/utilisateurs/{id}/         → update()
    PATCH  /api/utilisateurs/{id}/         → partial_update()
    DELETE /api/utilisateurs/{id}/        → destroy()
    GET    /api/utilisateurs/{id}/demandes/ → demandes()

DemandeViewSet:
    GET    /api/demandes/                  → list()
    POST   /api/demandes/                  → create()
    GET    /api/demandes/{id}/             → retrieve()
    PUT    /api/demandes/{id}/             → update()
    DELETE /api/demandes/{id}/             → destroy()
    POST   /api/demandes/{id}/soumettre/   → soumettre()
    POST   /api/demandes/{id}/assigner/    → assigner()
    POST   /api/demandes/{id}/changer-statut/ → changer_statut()
    GET    /api/demandes/statistiques/     → statistiques()

DocumentViewSet:
    GET    /api/documents/                 → list()
    POST   /api/documents/                 → create()
    GET    /api/documents/{id}/            → retrieve()
    DELETE /api/documents/{id}/            → destroy()
    POST   /api/documents/{id}/verifier/   → verifier()

NotificationViewSet:
    GET    /api/notifications/             → list()
    GET    /api/notifications/non-lues/    → non_lues()
    POST   /api/notifications/{id}/marquer-lu/ → marquer_lu()
    POST   /api/notifications/marquer-tout-lu/ → marquer_tout_lu()

AuthViewSet:
    POST   /api/auth/register/             → register()
    POST   /api/auth/login/                → login()
    POST   /api/auth/oauth/                → oauth()
    POST   /api/auth/refresh/              → refresh()
    POST   /api/auth/logout/               → logout()
    GET    /api/auth/me/                   → me()
    POST   /api/auth/change-password/     → change_password()
"""


# =============================================================================
# DEBUG: AFFICHAGE DES ROUTES
# =============================================================================

# En développement, on peut afficher les routes pour vérification
# from django.conf import settings
# if settings.DEBUG:
#     print("Routes API enregistrées:")
#     for url in urlpatterns:
#         print(f"  {url.pattern}")
