"""
Serializers pour les notifications
"""

from rest_framework import serializers

from ..models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer pour Notification.
    """
    type_display = serializers.CharField(source='get_type_notification_display', read_only=True)
    temps_ecoule = serializers.CharField(read_only=True)
    est_recente = serializers.BooleanField(read_only=True)
    icon = serializers.CharField(source='icon_par_defaut', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'message', 'type_notification', 'type_display',
            'lu', 'date_envoi', 'date_lecture',
            'temps_ecoule', 'est_recente',
            'lien', 'icon'
        ]


class NotificationMarkReadSerializer(serializers.ModelSerializer):
    """
    Serializer pour marquer une notification comme lue.
    """
    
    class Meta:
        model = Notification
        fields = ['lu']
