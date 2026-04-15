"""
Views pour les services administratifs (MVC Controller)
"""

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q

from ..models import ServiceAdministratif
from ..serializers import ServiceSerializer
from .base import BaseViewSet


class ServiceViewSet(BaseViewSet):
    """
    Controller pour les services administratifs.
    """
    queryset = ServiceAdministratif.objects.annotate(
        nombre_demandes_total=Count('demandes'),
        nombre_demandes_actives=Count('demandes', filter=~Q(
            demandes__statut__in=['validee', 'rejetee']
        ))
    ).all()
    serializer_class = ServiceSerializer
    filter_backends = [filters.SearchFilter]
    filterset_fields = ['actif']
    search_fields = ['nom_service', 'description']
    
    @action(detail=False, methods=['get'])
    def actifs(self, request):
        """
        GET /services/actifs/
        Retourne uniquement les services actifs.
        """
        services = ServiceAdministratif.services_actifs()
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        GET /services/statistiques/
        Statistiques des demandes par service.
        """
        stats = ServiceAdministratif.statistiques_demandes()
        data = []
        for service in stats:
            data.append({
                'service': service.nom_service,
                'total_demandes': service.total_demandes,
                'demandes_en_cours': service.demandes_en_cours
            })
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def desactiver(self, request, pk=None):
        """
        POST /services/{id}/desactiver/
        Désactive un service.
        """
        if not request.user.is_agent_or_admin:
            return Response({'error': 'Accès refusé'}, status=403)
        
        service = self.get_object()
        service.desactiver()
        return Response({'message': 'Service désactivé'})
    
    @action(detail=True, methods=['post'])
    def reactiver(self, request, pk=None):
        """
        POST /services/{id}/reactiver/
        Réactive un service.
        """
        if not request.user.is_agent_or_admin:
            return Response({'error': 'Accès refusé'}, status=403)
        
        service = self.get_object()
        service.reactiver()
        return Response({'message': 'Service réactivé'})
