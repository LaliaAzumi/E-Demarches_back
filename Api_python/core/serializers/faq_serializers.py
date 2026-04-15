"""
Serializers pour la FAQ
"""

from rest_framework import serializers

from ..models import FAQChatbot


class FAQSerializer(serializers.ModelSerializer):
    """
    Serializer pour FAQChatbot.
    """
    taux_utilite = serializers.FloatField(read_only=True)
    question_courte = serializers.CharField(read_only=True)
    
    class Meta:
        model = FAQChatbot
        fields = [
            'id', 'question', 'reponse', 'question_courte',
            'mots_cles', 'categorie',
            'ordre_affichage', 'actif',
            'vues', 'utile', 'taux_utilite'
        ]


class FAQSearchSerializer(serializers.Serializer):
    """
    Serializer pour la recherche FAQ.
    """
    query = serializers.CharField(required=True, min_length=2)
    categorie = serializers.CharField(required=False)
