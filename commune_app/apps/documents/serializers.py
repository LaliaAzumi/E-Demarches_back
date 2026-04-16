from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    demande_info = serializers.CharField(source='demande.type_demande', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'demande', 'demande_info', 'nom_fichier', 'type_document',
            'url', 'date_upload'
        ]
        read_only_fields = ['id', 'date_upload']


class DocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['demande', 'nom_fichier', 'type_document', 'url']
