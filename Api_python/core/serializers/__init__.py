"""
Package serializers - Conversion Modèles ↔ JSON
Exporte tous les serializers pour les Views
"""

# Utilisateurs
from .utilisateur_serializers import (
    UtilisateurSerializer,
    UtilisateurCreateSerializer,
    LoginSerializer,
    CustomRegisterSerializer,
    GoogleAuthSerializer,
)

# Profils
from .profil_serializers import (
    CitoyenSerializer,
    AgentSerializer,
    AdministrateurSerializer,
)

# Services et Demandes
from .demande_serializers import (
    ServiceSerializer,
    DemandeListSerializer,
    DemandeDetailSerializer,
    DemandeCreateSerializer,
    DemandeStatutUpdateSerializer,
)

# Documents
from .document_serializers import (
    DocumentSerializer,
    TraitementSerializer,
)

# Rendez-vous
from .rdv_serializers import (
    PropositionRDVSerializer,
    RendezVousSerializer,
    RendezVousCreateSerializer,
)

# Notifications
from .notification_serializers import (
    NotificationSerializer,
    NotificationMarkReadSerializer,
)

# FAQ
from .faq_serializers import (
    FAQSerializer,
    FAQSearchSerializer,
)

# Dashboard
from .dashboard_serializers import (
    DashboardStatsSerializer,
    DashboardCitoyenSerializer,
    DashboardAgentSerializer,
)

__all__ = [
    # Utilisateurs
    'UtilisateurSerializer', 'UtilisateurCreateSerializer', 'LoginSerializer',
    'CustomRegisterSerializer', 'GoogleAuthSerializer',
    # Profils
    'CitoyenSerializer', 'AgentSerializer', 'AdministrateurSerializer',
    # Services et Demandes
    'ServiceSerializer', 'DemandeListSerializer', 'DemandeDetailSerializer',
    'DemandeCreateSerializer', 'DemandeStatutUpdateSerializer',
    # Documents
    'DocumentSerializer', 'TraitementSerializer',
    # Rendez-vous
    'PropositionRDVSerializer', 'RendezVousSerializer', 'RendezVousCreateSerializer',
    # Notifications
    'NotificationSerializer', 'NotificationMarkReadSerializer',
    # FAQ
    'FAQSerializer', 'FAQSearchSerializer',
    # Dashboard
    'DashboardStatsSerializer', 'DashboardCitoyenSerializer', 'DashboardAgentSerializer',
]
