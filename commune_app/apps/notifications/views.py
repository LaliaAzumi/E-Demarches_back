from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer, NotificationCreateSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().select_related('utilisateur')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(utilisateur=self.request.user)

    @action(detail=True, methods=['post'])
    def marquer_lu(self, request, pk=None):
        notification = self.get_object()
        notification.lu = True
        notification.save()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['post'])
    def marquer_tout_lu(self, request):
        Notification.objects.filter(utilisateur=request.user, lu=False).update(lu=True)
        return Response({'message': 'Toutes les notifications marquées comme lues'})

    @action(detail=False, methods=['get'])
    def non_lues(self, request):
        notifications = self.get_queryset().filter(utilisateur=request.user, lu=False)
        serializer = NotificationSerializer(notifications, many=True)
        return Response({'count': notifications.count(), 'notifications': serializer.data})
