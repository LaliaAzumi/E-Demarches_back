from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Utilisateur, Citoyen, AgentAdministratif, ServiceAdministratif,
    DemandeAdministrative, Document, Traitement, PropositionRDV,
    RendezVous, Notification, Administrateur, FAQChatbot
)


@admin.register(Utilisateur)
class UtilisateurAdmin(BaseUserAdmin):
    list_display = ('email', 'nom', 'prenom', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenom', 'telephone', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'created_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom', 'prenom', 'telephone', 'role', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'nom', 'prenom')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(Citoyen)
class CitoyenAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'cin', 'adresse')
    search_fields = ('utilisateur__nom', 'utilisateur__prenom', 'cin')


@admin.register(AgentAdministratif)
class AgentAdministratifAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'matricule', 'service_affecte')
    search_fields = ('utilisateur__nom', 'utilisateur__prenom', 'matricule')


@admin.register(ServiceAdministratif)
class ServiceAdministratifAdmin(admin.ModelAdmin):
    list_display = ('nom_service', 'delai_traitement')
    search_fields = ('nom_service',)


@admin.register(DemandeAdministrative)
class DemandeAdministrativeAdmin(admin.ModelAdmin):
    list_display = ('id', 'id_demande', 'citoyen', 'type_demande', 'statut', 'date_demande')
    list_filter = ('type_demande', 'statut', 'service')
    search_fields = ('citoyen__utilisateur__nom', 'citoyen__utilisateur__prenom', 'citoyen__utilisateur__email', 'id_demande')
    date_hierarchy = 'date_demande'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('nom_document', 'type_document', 'demande', 'date_upload')
    list_filter = ('type_document',)
    search_fields = ('nom_document',)


@admin.register(Traitement)
class TraitementAdmin(admin.ModelAdmin):
    list_display = ('demande', 'agent', 'statut_apres_traitement', 'date_traitement')
    list_filter = ('statut_apres_traitement',)


@admin.register(PropositionRDV)
class PropositionRDVAdmin(admin.ModelAdmin):
    list_display = ('demande', 'date', 'heure', 'lieu', 'statut', 'agent')
    list_filter = ('statut',)
    date_hierarchy = 'date'


@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('id_rendez_vous', 'proposition', 'citoyen', 'statut', 'date_confirmation')
    list_filter = ('statut',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'type_notification', 'message', 'lu', 'date_envoi')
    list_filter = ('lu', 'type_notification')
    search_fields = ('utilisateur__nom', 'utilisateur__prenom', 'message')
    date_hierarchy = 'date_envoi'


@admin.register(Administrateur)
class AdministrateurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur',)
    search_fields = ('utilisateur__nom', 'utilisateur__prenom')


@admin.register(FAQChatbot)
class FAQChatbotAdmin(admin.ModelAdmin):
    list_display = ('question', 'created_at')
    search_fields = ('question', 'reponse')
