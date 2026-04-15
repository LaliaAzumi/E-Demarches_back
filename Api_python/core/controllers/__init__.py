"""
Package controllers - Controllers MVC
Exporte tous les ViewSets pour les URLs
"""

from .utilisateur_controller import UtilisateurViewSet
from .profil_controller import CitoyenViewSet, AgentViewSet, AdministrateurViewSet
from .service_controller import ServiceViewSet
from .demande_controller import DemandeViewSet
from .document_controller import DocumentViewSet, TraitementViewSet
from .rdv_controller import PropositionRDVViewSet, RendezVousViewSet
from .notification_controller import NotificationViewSet
from .faq_controller import FAQViewSet
from .dashboard_controller import dashboard_stats, dashboard_citoyen, dashboard_agent
from .auth_controller import GoogleAuthViewSet, AuthViewSet

__all__ = [
    # Utilisateurs
    'UtilisateurViewSet',
    # Profils
    'CitoyenViewSet', 'AgentViewSet', 'AdministrateurViewSet',
    # Services & Demandes
    'ServiceViewSet', 'DemandeViewSet',
    # Documents
    'DocumentViewSet', 'TraitementViewSet',
    # Rendez-vous
    'PropositionRDVViewSet', 'RendezVousViewSet',
    # Notifications
    'NotificationViewSet',
    # FAQ
    'FAQViewSet',
    # Dashboards
    'dashboard_stats', 'dashboard_citoyen', 'dashboard_agent',
    # Authentification OAuth
    'GoogleAuthViewSet', 'AuthViewSet',
]
