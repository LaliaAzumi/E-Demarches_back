"""
Serializers pour les documents et traitements
"""

from rest_framework import serializers

from ..models import Document, Traitement


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer pour Document.
    """
    type_display = serializers.CharField(source='get_type_document_display', read_only=True)
    taille_affichage = serializers.CharField(source='taille_fichier_affichage', read_only=True)
    extension = serializers.CharField(read_only=True)
    url = serializers.CharField(source='get_url', read_only=True)
    demande_id = serializers.PrimaryKeyRelatedField(
        queryset=Document.objects.all().values_list('demande', flat=True),
        source='demande',
        write_only=True
    )
    
    class Meta:
        model = Document
        fields = [
            'id', 'id_document', 'demande', 'demande_id',
            'nom_document', 'type_document', 'type_display',
            'fichier', 'url', 'extension', 'taille_affichage',
            'date_upload'
        ]
        read_only_fields = ['id_document', 'date_upload']


class TraitementSerializer(serializers.ModelSerializer):
    """
    Serializer pour Traitement.
    """
    agent_nom = serializers.CharField(source='agent.utilisateur.nom_complet', read_only=True)
    statut_display = serializers.CharField(
        source='get_statut_apres_traitement_display', 
        read_only=True
    )
    
    class Meta:
        model = Traitement
        fields = [
            'id', 'demande', 'agent', 'agent_nom',
            'commentaire', 'statut_apres_traitement', 'statut_display',
            'date_traitement'
        ]
