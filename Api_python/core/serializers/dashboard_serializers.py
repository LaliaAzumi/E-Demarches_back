"""
Serializers pour les dashboards
"""

from rest_framework import serializers

from .demande_serializers import DemandeListSerializer
from .rdv_serializers import RendezVousSerializer


class DashboardStatsSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques du dashboard admin.
    """
    total_demandes = serializers.IntegerField()
    demandes_en_attente = serializers.IntegerField()
    demandes_en_cours = serializers.IntegerField()
    demandes_validees = serializers.IntegerField()
    demandes_rejetees = serializers.IntegerField()
    total_citoyens = serializers.IntegerField()
    total_agents = serializers.IntegerField()
    rdv_a_venir = serializers.IntegerField()
    notifications_non_lues = serializers.IntegerField()


class DashboardCitoyenSerializer(serializers.Serializer):
    """
    Serializer pour le dashboard citoyen.
    """
    mes_demandes_total = serializers.IntegerField()
    mes_demandes_en_cours = serializers.IntegerField()
    mes_demandes_validees = serializers.IntegerField()
    mes_rdv = serializers.IntegerField()
    mes_notifications_non_lues = serializers.IntegerField()
    dernieres_demandes = DemandeListSerializer(many=True)
    prochains_rdv = RendezVousSerializer(many=True)


class DashboardAgentSerializer(serializers.Serializer):
    """
    Serializer pour le dashboard agent.
    """
    demandes_a_traiter = serializers.IntegerField()
    mes_traitements_ce_mois = serializers.IntegerField()
    propositions_rdv_a_venir = serializers.IntegerField()
    rdv_du_jour = serializers.IntegerField()
