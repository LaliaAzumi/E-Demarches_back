from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'utilisateur', 'message', 'lu', 'date_envoi']
    list_filter = ['lu', 'date_envoi']
    search_fields = ['message', 'utilisateur__email', 'utilisateur__nom']
    readonly_fields = ['date_envoi']
