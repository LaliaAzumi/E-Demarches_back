"""
Vues Web pour les Dashboards (Vues MVC - Rendu HTML)
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from ..models import (
    DemandeAdministrative, Citoyen, AgentAdministratif,
    RendezVous, Notification
)


class CitoyenDashboardView(LoginRequiredMixin, TemplateView):
    """
    Vue MVC - Dashboard Citoyen (Rendu HTML).
    Template: templates/core/dashboard_citoyen.html
    """
    template_name = 'core/dashboard_citoyen.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        from ..models import Citoyen
        
        context = super().get_context_data(**kwargs)
        
        try:
            citoyen = Citoyen.objects.get(utilisateur=self.request.user)
            demandes = DemandeAdministrative.objects.filter(citoyen=citoyen)
            rdv = RendezVous.objects.filter(citoyen=citoyen)
            
            context.update({
                'title': 'Mon Tableau de Bord',
                'citoyen': citoyen,
                'total_demandes': demandes.count(),
                'demandes_en_cours': demandes.filter(
                    statut__in=['en_attente', 'en_cours']
                ).count(),
                'demandes_validees': demandes.filter(statut='validee').count(),
                'total_rdv': rdv.count(),
                'prochains_rdv': rdv.order_by('proposition__date')[:5],
                'notifications_non_lues': Notification.non_lues(
                    self.request.user.id
                ).count(),
            })
        except Citoyen.DoesNotExist:
            context['error'] = 'Profil citoyen non trouvé'
        
        return context


class AgentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Vue MVC - Dashboard Agent (Rendu HTML).
    Template: templates/core/dashboard_agent.html
    """
    template_name = 'core/dashboard_agent.html'
    login_url = '/login/'
    
    def test_func(self):
        """Vérifie que l'utilisateur est agent ou admin."""
        return self.request.user.is_agent_or_admin
    
    def get_context_data(self, **kwargs):
        from ..models import Traitement, PropositionRDV
        from django.utils import timezone
        
        context = super().get_context_data(**kwargs)
        
        try:
            agent = AgentAdministratif.objects.get(
                utilisateur=self.request.user
            )
            
            context.update({
                'title': 'Tableau de Bord Agent',
                'agent': agent,
                'demandes_a_traiter': DemandeAdministrative.objects.filter(
                    statut='en_attente'
                ).count(),
                'mes_traitements': Traitement.objects.filter(agent=agent).count(),
                'traitements_ce_mois': Traitement.objects.filter(
                    agent=agent,
                    date_traitement__month=timezone.now().month
                ).count(),
                'propositions_rdv': PropositionRDV.objects.filter(
                    agent=agent,
                    statut='propose'
                ).count(),
                'rdv_du_jour': RendezVous.rdv_du_jour().count(),
            })
        except AgentAdministratif.DoesNotExist:
            context['error'] = 'Profil agent non trouvé'
        
        return context


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Vue MVC - Dashboard Admin (Rendu HTML).
    Template: templates/core/dashboard_admin.html
    """
    template_name = 'core/dashboard_admin.html'
    login_url = '/login/'
    
    def test_func(self):
        """Vérifie que l'utilisateur est admin."""
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            'title': 'Tableau de Bord Admin',
            'total_demandes': DemandeAdministrative.objects.count(),
            'demandes_en_attente': DemandeAdministrative.objects.filter(
                statut='en_attente'
            ).count(),
            'demandes_en_cours': DemandeAdministrative.objects.filter(
                statut='en_cours'
            ).count(),
            'demandes_validees': DemandeAdministrative.objects.filter(
                statut='validee'
            ).count(),
            'total_citoyens': Citoyen.objects.count(),
            'total_agents': AgentAdministratif.objects.count(),
            'rdv_a_venir': RendezVous.rdv_a_venir().count(),
        })
        
        return context
