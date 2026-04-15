"""
Views pour les notifications (MVC Controller)
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Notification
from ..serializers import NotificationSerializer, NotificationMarkReadSerializer
from .base import ReadOnlyViewSet


class NotificationViewSet(ReadOnlyViewSet):
    """
    Controller pour les notifications (lecture seule).
    Les utilisateurs ne peuvent que consulter et marquer comme lues.
    """
    serializer_class = NotificationSerializer
    filterset_fields = ['lu', 'type_notification']
    
    def get_queryset(self):
        """Retourne uniquement les notifications de l'utilisateur connecté."""
        return Notification.objects.filter(utilisateur=self.request.user)
    
    @action(detail=True, methods=['post'])
    def marquer_lu(self, request, pk=None):
        """
        POST /notifications/{id}/marquer_lu/
        Marque une notification comme lue.
        """
        notification = self.get_object()
        notification.marquer_lu()
        return Response({'message': 'Notification marquée comme lue'})
    
    @action(detail=False, methods=['post'])
    def marquer_tout_lu(self, request):
        """
        POST /notifications/marquer_tout_lu/
        Marque toutes les notifications comme lues.
        """
        count = Notification.marquer_tout_lu(request.user.id)
        return Response({'notifications_marquees': count})
    
    @action(detail=False, methods=['get'])
    def non_lues(self, request):
        """
        GET /notifications/non_lues/
        Retourne les notifications non lues.
        """
        notifications = Notification.non_lues(request.user.id)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def compteur(self, request):
        """
        GET /notifications/compteur/
        Retourne le nombre de notifications non lues.
        """
        count = Notification.non_lues(request.user.id).count()
        return Response({'non_lues': count})
    
    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """
        GET /notifications/recentes/
        Retourne les 10 notifications les plus récentes.
        """
        notifications = self.get_queryset()[:10]
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
