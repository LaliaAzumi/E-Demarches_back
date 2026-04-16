from rest_framework import serializers
from .models import Demande, Traitement, PropositionRDV, RendezVous


class TraitementSerializer(serializers.ModelSerializer):
    agent_nom = serializers.CharField(source='agent.utilisateur.nom', read_only=True)

    class Meta:
        model = Traitement
        fields = ['id', 'demande', 'agent', 'agent_nom', 'commentaire', 'statut_apres_traitement', 'date_traitement']
        read_only_fields = ['id', 'date_traitement']


class PropositionRDVSerializer(serializers.ModelSerializer):
    agent_nom = serializers.CharField(source='agent.utilisateur.nom', read_only=True)

    class Meta:
        model = PropositionRDV
        fields = ['id', 'demande', 'agent', 'agent_nom', 'date', 'heure', 'statut', 'created_at']
        read_only_fields = ['id', 'created_at']


class RendezVousSerializer(serializers.ModelSerializer):
    citoyen_nom = serializers.CharField(source='citoyen.utilisateur.nom', read_only=True)
    date = serializers.DateField(source='proposition.date', read_only=True)
    heure = serializers.TimeField(source='proposition.heure', read_only=True)

    class Meta:
        model = RendezVous
        fields = ['id', 'proposition', 'date', 'heure', 'citoyen', 'citoyen_nom', 'statut', 'date_confirmation']
        read_only_fields = ['id', 'date_confirmation']


class DemandeSerializer(serializers.ModelSerializer):
    citoyen_nom = serializers.CharField(source='citoyen.utilisateur.nom', read_only=True)
    citoyen_email = serializers.CharField(source='citoyen.utilisateur.email', read_only=True)
    traitements = TraitementSerializer(many=True, read_only=True)
    propositions_rdv = PropositionRDVSerializer(many=True, read_only=True)

    class Meta:
        model = Demande
        fields = [
            'id', 'type_demande', 'statut', 'date_demande',
            'citoyen', 'citoyen_nom', 'citoyen_email',
            'traitements', 'propositions_rdv'
        ]
        read_only_fields = ['id', 'date_demande']


class DemandeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Demande
        fields = ['type_demande']
