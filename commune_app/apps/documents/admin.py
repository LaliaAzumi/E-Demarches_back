from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'nom_fichier', 'type_document', 'demande', 'date_upload']
    list_filter = ['type_document', 'date_upload']
    search_fields = ['nom_fichier', 'demande__id']
    readonly_fields = ['date_upload']
