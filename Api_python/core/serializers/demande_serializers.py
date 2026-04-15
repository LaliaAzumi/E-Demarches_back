"""
Serializers pour les services et demandes administratives
"""

from rest_framework import serializers
from django.db.models import Count, Q

from ..models import ServiceAdministratif, DemandeAdministrative


class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer pour ServiceAdministratif.
    """
    nombre_demandes_actives = serializers.IntegerField(read_only=True)
    nombre_demandes_total = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ServiceAdministratif
        fields = [
            'id', 'nom_service', 'description',
            'delai_traitement', 'actif',
            'nombre_demandes_actives', 'nombre_demandes_total',
            'created_at', 'updated_at'
        ]


class DemandeListSerializer(serializers.ModelSerializer):
    """
    Serializer liste pour DemandeAdministrative (vue réduite).
    """
    citoyen_nom = serializers.CharField(source='citoyen.nom_complet', read_only=True)
    service_nom = serializers.CharField(source='service.nom_service', read_only=True)
    type_display = serializers.CharField(source='get_type_demande_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    nombre_documents = serializers.SerializerMethodField()
    a_propositions_rdv = serializers.BooleanField(source='a_propositions_rdv', read_only=True)
    
    class Meta:
        model = DemandeAdministrative
        fields = [
            'id', 'id_demande', 'citoyen_nom', 'service_nom',
            'type_demande', 'type_display',
            'statut', 'statut_display',
            'date_demande', 'nombre_documents', 'a_propositions_rdv'
        ]
    
    def get_nombre_documents(self, obj):
        return obj.nombre_documents()


class DemandeDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détail pour DemandeAdministrative.
    """
    citoyen = serializers.SerializerMethodField()
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceAdministratif.objects.all(),
        source='service',
        write_only=True,
        required=False,
        allow_null=True
    )
    type_display = serializers.CharField(source='get_type_demande_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    documents_count = serializers.SerializerMethodField()
    propositions_rdv = serializers.SerializerMethodField()
    
    class Meta:
        model = DemandeAdministrative
        fields = [
            'id', 'id_demande', 'citoyen', 'service', 'service_id',
            'type_demande', 'type_display',
            'statut', 'statut_display', 'motif_rejet',
            'date_demande', 'documents_count',
            'propositions_rdv',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id_demande', 'date_demande']
    
    def get_citoyen(self, obj):
        """Retourne les données du citoyen."""
        from .profil_serializers import CitoyenSerializer
        return CitoyenSerializer(obj.citoyen).data
    
    def get_documents_count(self, obj):
        return obj.nombre_documents()
    
    def get_propositions_rdv(self, obj):
        """Retourne les propositions de RDV actives."""
        from .rdv_serializers import PropositionRDVSerializer
        propositions = obj.propositions_rdv_actives()
        return PropositionRDVSerializer(propositions, many=True).data


class DemandeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer une demande.
    """
    class Meta:
        model = DemandeAdministrative
        fields = ['type_demande', 'service']


class DemandeStatutUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour mettre à jour le statut d'une demande.
    """
    motif = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = DemandeAdministrative
        fields = ['statut', 'motif']
    
    def update(self, instance, validated_data):
        motif = validated_data.pop('motif', None)
        nouveau_statut = validated_data.get('statut')
        
        instance.changer_statut(nouveau_statut, motif)
        return instance
