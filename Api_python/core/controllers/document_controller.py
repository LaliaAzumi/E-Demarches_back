"""
Views pour les documents et traitements (MVC Controller)
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count

from ..models import Document, Traitement, AgentAdministratif
from ..serializers import DocumentSerializer, TraitementSerializer
from .base import BaseViewSet


class DocumentViewSet(BaseViewSet):
    """
    Controller pour les documents.
    """
    queryset = Document.objects.select_related('demande').all()
    serializer_class = DocumentSerializer
    filterset_fields = ['type_document', 'demande']


class TraitementViewSet(BaseViewSet):
    """
    Controller pour les traitements des demandes.
    """
    queryset = Traitement.objects.select_related('demande', 'agent').all()
    serializer_class = TraitementSerializer
    filterset_fields = ['demande', 'agent', 'statut_apres_traitement']
    
    def perform_create(self, serializer):
        """Enregistre l'agent connecté comme traitant."""
        try:
            agent = AgentAdministratif.objects.get(utilisateur=self.request.user)
            serializer.save(agent=agent)
        except AgentAdministratif.DoesNotExist:
            pass
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def mes_traitements(self, request):
        """
        GET /traitements/mes_traitements/
        Retourne les traitements de l'agent connecté.
        """
        try:
            agent = AgentAdministratif.objects.get(utilisateur=request.user)
        except AgentAdministratif.DoesNotExist:
            return Response([])
        
        traitements = Traitement.objects.filter(agent=agent)
        serializer = TraitementSerializer(traitements, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        GET /traitements/statistiques/
        Statistiques des traitements.
        """
        stats = Traitement.statistiques_mensuelles()
        return Response(list(stats))
    
    @action(detail=False, methods=['get'])
    def ce_mois(self, request):
        """
        GET /traitements/ce_mois/
        Traitements du mois en cours.
        """
        from django.utils import timezone
        traitements = Traitement.objects.filter(
            date_traitement__month=timezone.now().month,
            date_traitement__year=timezone.now().year
        )
        serializer = TraitementSerializer(traitements, many=True)
        return Response(serializer.data)
