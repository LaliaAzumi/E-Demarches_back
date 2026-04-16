from django.contrib import admin
from .models import Statistique


@admin.register(Statistique)
class StatistiqueAdmin(admin.ModelAdmin):
    list_display = ['type_stat', 'categorie', 'valeur', 'date', 'date_mise_a_jour']
    list_filter = ['type_stat', 'date']
    search_fields = ['categorie', 'type_stat']
    date_hierarchy = 'date'
