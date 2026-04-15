"""
Vues pour les pages statiques (Vues MVC - Rendu HTML)
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(TemplateView):
    """
    Vue MVC - Page d'accueil.
    Template: templates/core/home.html
    """
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        """Prépare le contexte pour la vue."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Accueil - Administration'
        context['services_count'] = 5  # À remplacer par requête DB
        return context


class AboutView(TemplateView):
    """
    Vue MVC - Page à propos.
    Template: templates/core/about.html
    """
    template_name = 'core/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'À propos'
        return context


class ContactView(TemplateView):
    """
    Vue MVC - Page contact.
    Template: templates/core/contact.html
    """
    template_name = 'core/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Contact'
        return context


class LoginView(TemplateView):
    """
    Vue MVC - Page de connexion.
    Template: templates/core/login.html
    """
    template_name = 'core/login.html'


class RegisterView(TemplateView):
    """
    Vue MVC - Page d'inscription.
    Template: templates/core/register.html
    """
    template_name = 'core/register.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Vue MVC - Page profil utilisateur (nécessite connexion).
    Template: templates/core/profile.html
    """
    template_name = 'core/profile.html'
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
