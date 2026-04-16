from django.contrib import admin
from .models import Demande, Traitement, PropositionRDV, RendezVous


@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = ['id', 'type_demande', 'citoyen', 'statut', 'date_demande']
    list_filter = ['type_demande', 'statut', 'date_demande']
    search_fields = ['id', 'citoyen__utilisateur__nom', 'citoyen__utilisateur__email']
    date_hierarchy = 'date_demande'
    readonly_fields = ['date_demande']


@admin.register(Traitement)
class TraitementAdmin(admin.ModelAdmin):
    list_display = ['id', 'demande', 'agent', 'statut_apres_traitement', 'date_traitement']
    list_filter = ['statut_apres_traitement', 'date_traitement']
    search_fields = ['demande__id', 'agent__utilisateur__nom', 'commentaire']
    readonly_fields = ['date_traitement']


@admin.register(PropositionRDV)
class PropositionRDVAdmin(admin.ModelAdmin):
    list_display = ['id', 'demande', 'agent', 'date', 'heure', 'statut', 'created_at']
    list_filter = ['statut', 'date']
    search_fields = ['demande__id', 'agent__utilisateur__nom']
    readonly_fields = ['created_at']


@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ['id', 'proposition', 'citoyen', 'statut', 'date_confirmation']
    list_filter = ['statut', 'date_confirmation']
    search_fields = ['proposition__demande__id', 'citoyen__utilisateur__nom']
    readonly_fields = ['date_confirmation']
