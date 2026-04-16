"""
================================================================================
FICHIER: urls.py (Projet)
PROJET: Api_python
RÔLE: Routage URL principal

ARCHITECTURE:
    Ce fichier définit les routes URL à la racine du projet.
    Il inclut les URLs des applications et des services tiers.

    ORGANISATION:
        /admin/         → Interface d'administration Django
        /api/           → API REST (inclus depuis core.urls)
        /api/auth/      → Authentification dj-rest-auth

    NAMESPACE:
        Toutes les routes API sont préfixées par /api/

AGILE: URLs = API Endpoints disponibles
================================================================================
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# =============================================================================
# URL PATTERNS PRINCIPAUX
# =============================================================================

urlpatterns = [
    # Administration Django
    path('admin/', admin.site.urls),
    
    # API Principale (notre application)
    path('api/', include('core.urls')),
    
    # Authentification dj-rest-auth (login/logout/password)
    # Note: registration est gérée par notre propre view
    path('api/auth/', include('dj_rest_auth.urls')),
    
    # OAuth (allauth)
    path('api/oauth/', include('allauth.socialaccount.urls')),
]

# =============================================================================
# FICHIERS STATIQUES ET MÉDIAS (Développement uniquement)
# =============================================================================

if settings.DEBUG:
    # Servir les fichiers médias et statiques en développement
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# =============================================================================
# GESTION DES ERREURS 404 ET 500
# =============================================================================

# Handler personnalisés (optionnels)
# handler404 = 'core.views.errors.custom_404'
# handler500 = 'core.views.errors.custom_500'

# =============================================================================
# NOTES SUR L'ARCHITECTURE URL
# =============================================================================

"""
STRUCTURE COMPLÈTE DES URLS:

Authentification:
    POST   /api/auth/register/           → Inscription
    POST   /api/auth/login/              → Connexion
    POST   /api/auth/oauth/              → OAuth (Google)
    POST   /api/auth/refresh/            → Rafraîchir token
    POST   /api/auth/logout/             → Déconnexion
    GET    /api/auth/me/                 → Profil connecté
    POST   /api/auth/change-password/    → Changer mot de passe
    POST   /api/auth/password/reset/     → Demande réinitialisation
    POST   /api/auth/password/reset/confirm/ → Confirmer réinitialisation

Utilisateurs:
    GET    /api/utilisateurs/            → Liste (admin)
    GET    /api/utilisateurs/{id}/       → Détail
    PUT    /api/utilisateurs/{id}/       → Modifier
    DELETE /api/utilisateurs/{id}/        → Désactiver
    GET    /api/utilisateurs/{id}/demandes/ → Demandes du citoyen

Demandes:
    GET    /api/demandes/                → Liste
    POST   /api/demandes/                → Créer
    GET    /api/demandes/{id}/           → Détail
    PUT    /api/demandes/{id}/           → Modifier
    DELETE /api/demandes/{id}/           → Supprimer
    POST   /api/demandes/{id}/soumettre/ → Soumettre
    POST   /api/demandes/{id}/assigner/  → Assigner agent
    POST   /api/demandes/{id}/changer-statut/ → Changer statut
    GET    /api/demandes/statistiques/   → Statistiques

Documents:
    GET    /api/documents/?demande_id=1  → Liste
    POST   /api/documents/               → Upload
    GET    /api/documents/{id}/          → Détail
    DELETE /api/documents/{id}/          → Supprimer
    POST   /api/documents/{id}/verifier/ → Vérifier

Notifications:
    GET    /api/notifications/           → Liste
    GET    /api/notifications/non-lues/  → Compter non lues
    POST   /api/notifications/{id}/marquer-lu/ → Marquer lu
    POST   /api/notifications/marquer-tout-lu/ → Tout lu

Services:
    GET    /api/services/                → Liste des services
    GET    /api/services/{id}/           → Détail service

Rendez-vous:
    GET    /api/rendez-vous/             → Liste
    POST   /api/rendez-vous/             → Créer proposition
    GET    /api/rendez-vous/{id}/        → Détail
    POST   /api/rendez-vous/{id}/confirmer/ → Confirmer
    POST   /api/rendez-vous/{id}/annuler/   → Annuler
"""
