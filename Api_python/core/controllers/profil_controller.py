"""
Views pour les profils (Citoyen, Agent, Administrateur) - MVC Controller
"""

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from ..models import Citoyen, AgentAdministratif, Administrateur
from ..serializers import CitoyenSerializer, AgentSerializer, AdministrateurSerializer
from .base import BaseViewSet


class CitoyenViewSet(BaseViewSet):
    """
    Controller pour gérer les profils citoyens.
    """
    queryset = Citoyen.objects.select_related('utilisateur').all()
    serializer_class = CitoyenSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['utilisateur__nom', 'utilisateur__prenom', 'ville', 'code_postal']
    
    def get_queryset(self):
        """
        Les citoyens ne voient que leur profil.
        Les agents/admins voient tous les profils.
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_agent_or_admin:
            queryset = queryset.filter(utilisateur=user)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def demandes(self, request, pk=None):
        """
        GET /citoyens/{id}/demandes/
        Retourne les demandes du citoyen.
        """
        citoyen = self.get_object()
        from ..serializers import DemandeListSerializer
        demandes = citoyen.demandes.all()
        serializer = DemandeListSerializer(demandes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rdv(self, request, pk=None):
        """
        GET /citoyens/{id}/rdv/
        Retourne les rendez-vous du citoyen.
        """
        citoyen = self.get_object()
        from ..serializers import RendezVousSerializer
        rdvs = citoyen.rendez_vous.all()
        serializer = RendezVousSerializer(rdvs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mon_profil(self, request):
        """
        GET /citoyens/mon_profil/
        Retourne le profil du citoyen connecté.
        """
        try:
            citoyen = Citoyen.objects.get(utilisateur=request.user)
            serializer = self.get_serializer(citoyen)
            return Response(serializer.data)
        except Citoyen.DoesNotExist:
            return Response({'error': 'Profil citoyen non trouvé'}, status=404)


class AgentViewSet(BaseViewSet):
    """
    Controller pour gérer les profils agents.
    """
    queryset = AgentAdministratif.objects.select_related('utilisateur').all()
    serializer_class = AgentSerializer
    filter_backends = [filters.SearchFilter]
    filterset_fields = ['departement', 'statut']
    search_fields = ['utilisateur__nom', 'utilisateur__prenom', 'matricule']
    
    def get_queryset(self):
        """Filtre selon les permissions."""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role == 'agent':
            queryset = queryset.filter(utilisateur=user)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def traitements(self, request, pk=None):
        """
        GET /agents/{id}/traitements/
        Retourne les traitements de l'agent.
        """
        agent = self.get_object()
        from ..serializers import TraitementSerializer
        traitements = agent.traitements.all()
        serializer = TraitementSerializer(traitements, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mon_profil(self, request):
        """
        GET /agents/mon_profil/
        Retourne le profil de l'agent connecté.
        """
        try:
            agent = AgentAdministratif.objects.get(utilisateur=request.user)
            serializer = self.get_serializer(agent)
            return Response(serializer.data)
        except AgentAdministratif.DoesNotExist:
            return Response({'error': 'Profil agent non trouvé'}, status=404)


class AdministrateurViewSet(BaseViewSet):
    """
    Controller pour gérer les administrateurs.
    Accessible uniquement aux admins.
    """
    queryset = Administrateur.objects.select_related('utilisateur').all()
    serializer_class = AdministrateurSerializer
    permission_classes = [IsAdminUser]
