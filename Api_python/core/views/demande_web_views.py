"""
Vues Web pour les demandes (Vues MVC - Rendu HTML)
Séparées des Contrôleurs API dans controllers/
"""

from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from ..models import DemandeAdministrative, ServiceAdministratif


class DemandeListView(LoginRequiredMixin, ListView):
    """
    Vue MVC - Liste des demandes (Rendu HTML).
    Template: templates/core/demande_list.html
    """
    model = DemandeAdministrative
    template_name = 'core/demande_list.html'
    context_object_name = 'demandes'
    paginate_by = 10
    login_url = '/login/'
    
    def get_queryset(self):
        """Filtre selon l'utilisateur connecté."""
        queryset = super().get_queryset()
        
        if not self.request.user.is_agent_or_admin:
            # Citoyen: ses demandes uniquement
            queryset = queryset.filter(citoyen__utilisateur=self.request.user)
        
        return queryset.select_related('citoyen', 'service')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mes Demandes'
        context['total_demandes'] = self.get_queryset().count()
        return context


class DemandeDetailView(LoginRequiredMixin, DetailView):
    """
    Vue MVC - Détail d'une demande (Rendu HTML).
    Template: templates/core/demande_detail.html
    """
    model = DemandeAdministrative
    template_name = 'core/demande_detail.html'
    context_object_name = 'demande'
    pk_url_kwarg = 'pk'
    login_url = '/login/'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if not self.request.user.is_agent_or_admin:
            queryset = queryset.filter(citoyen__utilisateur=self.request.user)
        
        return queryset.select_related('citoyen', 'service').prefetch_related('documents')


class DemandeCreateView(LoginRequiredMixin, CreateView):
    """
    Vue MVC - Créer une demande (Rendu HTML).
    Template: templates/core/demande_form.html
    """
    model = DemandeAdministrative
    template_name = 'core/demande_form.html'
    fields = ['type_demande', 'service']
    success_url = reverse_lazy('demande-list')
    login_url = '/login/'
    
    def form_valid(self, form):
        """Associe la demande au citoyen connecté."""
        from ..models import Citoyen
        
        try:
            citoyen = Citoyen.objects.get(utilisateur=self.request.user)
            form.instance.citoyen = citoyen
        except Citoyen.DoesNotExist:
            form.add_error(None, "Vous devez être un citoyen pour créer une demande")
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nouvelle Demande'
        context['services'] = ServiceAdministratif.services_actifs()
        return context


class ServiceListView(ListView):
    """
    Vue MVC - Liste des services (Rendu HTML).
    Template: templates/core/service_list.html
    """
    model = ServiceAdministratif
    template_name = 'core/service_list.html'
    context_object_name = 'services'
    
    def get_queryset(self):
        return ServiceAdministratif.services_actifs()
