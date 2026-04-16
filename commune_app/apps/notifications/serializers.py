from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source='utilisateur.nom', read_only=True)
    utilisateur_email = serializers.CharField(source='utilisateur.email', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'utilisateur', 'utilisateur_nom', 'utilisateur_email',
            'message', 'lu', 'date_envoi'
        ]
        read_only_fields = ['id', 'date_envoi']


class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['utilisateur', 'message']
