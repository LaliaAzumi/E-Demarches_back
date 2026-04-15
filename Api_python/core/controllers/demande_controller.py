"""
Views pour les demandes administratives (MVC Controller)
"""

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count, Q

from ..models import DemandeAdministrative, Citoyen, AgentAdministratif
from ..serializers import (
    DemandeListSerializer,
    DemandeDetailSerializer,
    DemandeCreateSerializer,
    DemandeStatutUpdateSerializer,
    DocumentSerializer
)
from .base import BaseViewSet


class DemandeViewSet(BaseViewSet):
    """
    Controller pour les demandes administratives.
    Gère le workflow complet des demandes.
    """
    queryset = DemandeAdministrative.objects.select_related(
        'citoyen', 'citoyen__utilisateur', 'service'
    ).prefetch_related('documents', 'propositions_rdv').all()
    serializer_class = DemandeDetailSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_demande', 'statut', 'citoyen', 'service']
    search_fields = ['id_demande', 'motif_rejet']
    ordering_fields = ['date_demande', 'created_at', 'updated_at']
    ordering = ['-date_demande']
    
    def get_serializer_class(self):
        """Sélectionne le serializer selon l'action."""
        if self.action == 'list':
            return DemandeListSerializer
        elif self.action == 'create':
            return DemandeCreateSerializer
        return DemandeDetailSerializer
    
    def get_queryset(self):
        """
        Filtre selon le rôle de l'utilisateur.
        Citoyen: ses demandes uniquement.
        Agent/Admin: toutes les demandes.
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_agent_or_admin:
            try:
                citoyen = Citoyen.objects.get(utilisateur=user)
                queryset = queryset.filter(citoyen=citoyen)
            except Citoyen.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    def perform_create(self, serializer):
        """Crée une demande pour le citoyen connecté."""
        try:
            citoyen = Citoyen.objects.get(utilisateur=self.request.user)
        except Citoyen.DoesNotExist:
            raise PermissionDenied("Vous devez être un citoyen pour créer une demande")
        
        serializer.save(citoyen=citoyen)
    
    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        """
        POST /demandes/{id}/changer_statut/
        Change le statut d'une demande (agents/admins uniquement).
        """
        if not request.user.is_agent_or_admin:
            raise PermissionDenied("Vous n'avez pas les droits pour changer le statut")
        
        demande = self.get_object()
        serializer = DemandeStatutUpdateSerializer(demande, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Statut mis à jour',
            'demande': DemandeDetailSerializer(demande).data
        })
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """
        GET /demandes/{id}/documents/
        Retourne les documents d'une demande.
        """
        demande = self.get_object()
        documents = demande.documents.all()
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def ajouter_document(self, request, pk=None):
        """
        POST /demandes/{id}/ajouter_document/
        Ajoute un document à une demande.
        """
        demande = self.get_object()
        serializer = DocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(demande=demande)
        return Response(serializer.data, status=201)
    
    @action(detail=True, methods=['get'])
    def propositions_rdv(self, request, pk=None):
        """
        GET /demandes/{id}/propositions_rdv/
        Retourne les propositions de RDV.
        """
        demande = self.get_object()
        from ..serializers import PropositionRDVSerializer
        propositions = demande.propositions_rdv.all()
        serializer = PropositionRDVSerializer(propositions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mes_demandes(self, request):
        """
        GET /demandes/mes_demandes/
        Retourne les demandes du citoyen connecté.
        """
        try:
            citoyen = Citoyen.objects.get(utilisateur=request.user)
        except Citoyen.DoesNotExist:
            return Response([])
        
        demandes = DemandeAdministrative.objects.filter(citoyen=citoyen)
        serializer = DemandeListSerializer(demandes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def a_traiter(self, request):
        """
        GET /demandes/a_traiter/
        Retourne les demandes en attente (agents uniquement).
        """
        if not request.user.is_agent_or_admin:
            return Response({'error': 'Accès refusé'}, status=403)
        
        demandes = DemandeAdministrative.objects.filter(statut='en_attente')
        serializer = DemandeListSerializer(demandes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        GET /demandes/statistiques/
        Statistiques des demandes.
        """
        par_statut = DemandeAdministrative.statistiques_par_statut()
        par_type = DemandeAdministrative.statistiques_par_type()
        
        return Response({
            'par_statut': list(par_statut),
            'par_type': list(par_type)
        })
