"""
Package views - Vues Django traditionnelles (HTML/Templates)
Véritables vues MVC pour le rendu côté serveur
"""

from .home_views import HomeView, AboutView, ContactView
from .demande_web_views import (
    DemandeListView,
    DemandeDetailView,
    DemandeCreateView,
)
from .dashboard_web_views import (
    CitoyenDashboardView,
    AgentDashboardView,
    AdminDashboardView,
)

__all__ = [
    # Pages statiques
    'HomeView', 'AboutView', 'ContactView',
    # Vues Demandes (Web)
    'DemandeListView', 'DemandeDetailView', 'DemandeCreateView',
    # Dashboards (Web)
    'CitoyenDashboardView', 'AgentDashboardView', 'AdminDashboardView',
]
