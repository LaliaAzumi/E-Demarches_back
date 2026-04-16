from rest_framework import serializers
from .models import Statistique


class StatistiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Statistique
        fields = ['id', 'date', 'type_stat', 'categorie', 'valeur', 'details', 'date_mise_a_jour']
        read_only_fields = ['id', 'date_mise_a_jour']


class StatistiqueGlobaleSerializer(serializers.Serializer):
    total_demandes = serializers.IntegerField()
    demandes_par_statut = serializers.DictField(child=serializers.IntegerField())
    demandes_par_type = serializers.DictField(child=serializers.IntegerField())
    total_utilisateurs = serializers.IntegerField()
    utilisateurs_par_role = serializers.DictField(child=serializers.IntegerField())
    total_documents = serializers.IntegerField()
    total_traitements = serializers.IntegerField()
