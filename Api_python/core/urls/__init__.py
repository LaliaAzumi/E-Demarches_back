"""
Package urls - Routes API
Assemble toutes les routes des différents modules
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

# Import des Controllers (MVC)
from ..controllers import (
    UtilisateurViewSet,
    CitoyenViewSet, AgentViewSet, AdministrateurViewSet,
    ServiceViewSet, DemandeViewSet,
    DocumentViewSet, TraitementViewSet,
    PropositionRDVViewSet, RendezVousViewSet,
    NotificationViewSet, FAQViewSet,
    dashboard_stats, dashboard_citoyen, dashboard_agent,
    GoogleAuthViewSet, AuthViewSet,
)

# Créer le routeur principal
router = DefaultRouter()

# Enregistrer les ViewSets
router.register(r'utilisateurs', UtilisateurViewSet, basename='utilisateur')
router.register(r'citoyens', CitoyenViewSet, basename='citoyen')
router.register(r'agents', AgentViewSet, basename='agent')
router.register(r'administrateurs', AdministrateurViewSet, basename='administrateur')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'demandes', DemandeViewSet, basename='demande')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'traitements', TraitementViewSet, basename='traitement')
router.register(r'propositions-rdv', PropositionRDVViewSet, basename='proposition-rdv')
router.register(r'rendez-vous', RendezVousViewSet, basename='rendez-vous')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'faq', FAQViewSet, basename='faq')

# URLs principales
urlpatterns = [
    # Routes du routeur
    path('', include(router.urls)),
    
    # Authentification JWT
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Authentification OAuth Google
    path('auth/google/login/', GoogleAuthViewSet.as_view({'post': 'google_login'}), name='google-login'),
    path('auth/google/verify/', GoogleAuthViewSet.as_view({'post': 'verify_token'}), name='google-verify'),
    path('auth/refresh/', AuthViewSet.as_view({'post': 'refresh_token'}), name='auth-refresh'),
    path('auth/logout/', AuthViewSet.as_view({'post': 'logout'}), name='auth-logout'),
    path('auth/me/', AuthViewSet.as_view({'get': 'me'}), name='auth-me'),
    
    # dj-rest-auth endpoints
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # Dashboards
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path('dashboard/citoyen/', dashboard_citoyen, name='dashboard-citoyen'),
    path('dashboard/agent/', dashboard_agent, name='dashboard-agent'),
]
