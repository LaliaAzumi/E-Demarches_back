"""
Serializers pour les rendez-vous
"""

from rest_framework import serializers

from ..models import PropositionRDV, RendezVous


class PropositionRDVSerializer(serializers.ModelSerializer):
    """
    Serializer pour PropositionRDV.
    """
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    est_disponible = serializers.BooleanField(read_only=True)
    est_expire = serializers.BooleanField(read_only=True)
    datetime_complet = serializers.DateTimeField(read_only=True)
    agent_nom = serializers.CharField(source='agent.utilisateur.nom_complet', read_only=True)
    
    class Meta:
        model = PropositionRDV
        fields = [
            'id', 'demande', 'agent', 'agent_nom',
            'date', 'heure', 'datetime_complet', 'lieu',
            'statut', 'statut_display',
            'est_disponible', 'est_expire',
            'created_at'
        ]


class RendezVousSerializer(serializers.ModelSerializer):
    """
    Serializer pour RendezVous.
    """
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    date_rdv = serializers.DateField(read_only=True)
    heure_rdv = serializers.TimeField(read_only=True)
    lieu_rdv = serializers.CharField(read_only=True)
    agent_nom = serializers.CharField(source='agent_rdv.utilisateur.nom_complet', read_only=True)
    peut_annuler = serializers.BooleanField(read_only=True)
    est_passe = serializers.BooleanField(read_only=True)
    proposition = PropositionRDVSerializer(read_only=True)
    
    class Meta:
        model = RendezVous
        fields = [
            'id', 'id_rendez_vous', 'proposition',
            'date_rdv', 'heure_rdv', 'lieu_rdv', 'agent_nom',
            'statut', 'statut_display',
            'peut_annuler', 'est_passe',
            'date_confirmation', 'notes'
        ]


class RendezVousCreateSerializer(serializers.Serializer):
    """
    Serializer pour créer un rendez-vous à partir d'une proposition.
    """
    proposition_id = serializers.IntegerField()
    
    def validate_proposition_id(self, value):
        from ..models import PropositionRDV
        try:
            proposition = PropositionRDV.objects.get(id=value)
        except PropositionRDV.DoesNotExist:
            raise serializers.ValidationError("Proposition non trouvée")
        
        if not proposition.est_disponible:
            raise serializers.ValidationError("Cette proposition n'est plus disponible")
        
        return value
    
    def create(self, validated_data):
        from ..models import PropositionRDV, Citoyen
        
        proposition = PropositionRDV.objects.get(id=validated_data['proposition_id'])
        citoyen = Citoyen.objects.get(utilisateur=self.context['request'].user)
        
        # Marquer la proposition comme choisie
        proposition.marquer_choisi()
        
        # Créer le rendez-vous
        rdv = RendezVous.objects.create(
            proposition=proposition,
            citoyen=citoyen
        )
        
        return rdv
