from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Utilisateur, Citoyen, Agent


@admin.register(Utilisateur)
class UtilisateurAdmin(BaseUserAdmin):
    list_display = ['id', 'email', 'nom', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['email', 'nom']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'created_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(Citoyen)
class CitoyenAdmin(admin.ModelAdmin):
    list_display = ['id', 'utilisateur', 'cin', 'adresse']
    list_filter = ['utilisateur__is_active']
    search_fields = ['utilisateur__email', 'utilisateur__nom', 'cin']


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['id', 'utilisateur', 'matricule', 'service']
    list_filter = ['utilisateur__is_active']
    search_fields = ['utilisateur__email', 'utilisateur__nom', 'matricule']
