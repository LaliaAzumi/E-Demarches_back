"""
Views pour les rendez-vous (MVC Controller)
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from datetime import date

from ..models import PropositionRDV, RendezVous, Citoyen, AgentAdministratif
from ..serializers import PropositionRDVSerializer, RendezVousSerializer
from .base import BaseViewSet


class PropositionRDVViewSet(BaseViewSet):
    """
    Controller pour les propositions de rendez-vous.
    """
    queryset = PropositionRDV.objects.select_related('demande', 'agent').all()
    serializer_class = PropositionRDVSerializer
    filterset_fields = ['demande', 'statut', 'date']
    
    def perform_create(self, serializer):
        """Crée une proposition par un agent."""
        if not self.request.user.is_agent_or_admin:
            raise PermissionDenied("Seuls les agents peuvent proposer des RDV")
        
        try:
            agent = AgentAdministratif.objects.get(utilisateur=self.request.user)
        except AgentAdministratif.DoesNotExist:
            raise PermissionDenied("Vous n'êtes pas un agent")
        
        serializer.save(agent=agent)
    
    @action(detail=True, methods=['post'])
    def choisir(self, request, pk=None):
        """
        POST /propositions-rdv/{id}/choisir/
        Choisir cette proposition de RDV (citoyen uniquement).
        """
        proposition = self.get_object()
        
        try:
            citoyen = Citoyen.objects.get(utilisateur=request.user)
        except Citoyen.DoesNotExist:
            raise PermissionDenied("Vous devez être un citoyen")
        
        # Vérifier que la proposition correspond à une demande du citoyen
        if proposition.demande.citoyen != citoyen:
            raise PermissionDenied("Cette proposition ne vous concerne pas")
        
        proposition.marquer_choisi()
        
        # Créer le rendez-vous
        rdv = RendezVous.objects.create(proposition=proposition, citoyen=citoyen)
        
        return Response({
            'message': 'Rendez-vous confirmé',
            'rendez_vous': RendezVousSerializer(rdv).data
        })
    
    @action(detail=False, methods=['post'])
    def marquer_expires(self, request):
        """
        POST /propositions-rdv/marquer_expires/
        Marque automatiquement les propositions expirées.
        """
        if not request.user.is_staff:
            raise PermissionDenied()
        
        count = PropositionRDV.marquer_expires()
        return Response({'propositions_expirees': count})
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """
        GET /propositions-rdv/disponibles/
        Retourne les propositions encore valides.
        """
        propositions = PropositionRDV.propositions_actives()
        serializer = PropositionRDVSerializer(propositions, many=True)
        return Response(serializer.data)


class RendezVousViewSet(BaseViewSet):
    """
    Controller pour les rendez-vous confirmés.
    """
    queryset = RendezVous.objects.select_related(
        'proposition', 'proposition__agent', 'proposition__demande', 'citoyen'
    ).all()
    serializer_class = RendezVousSerializer
    filterset_fields = ['statut', 'citoyen']
    
    def perform_create(self, serializer):
        """Crée un rendez-vous pour le citoyen connecté."""
        try:
            citoyen = Citoyen.objects.get(utilisateur=self.request.user)
        except Citoyen.DoesNotExist:
            raise PermissionDenied("Vous devez être un citoyen")
        
        serializer.save(citoyen=citoyen)
    
    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """
        POST /rendez-vous/{id}/annuler/
        Annule un rendez-vous.
        """
        rdv = self.get_object()
        raison = request.data.get('raison', '')
        
        # Vérifier les droits
        is_citoyen = request.user == rdv.citoyen.utilisateur
        is_agent = request.user == rdv.agent_rdv.utilisateur if rdv.agent_rdv else False
        
        if not (is_citoyen or is_agent or request.user.is_staff):
            raise PermissionDenied("Vous ne pouvez pas annuler ce rendez-vous")
        
        rdv.annuler(raison=raison, par_citoyen=is_citoyen)
        return Response({'message': 'Rendez-vous annulé'})
    
    @action(detail=False, methods=['get'])
    def a_venir(self, request):
        """
        GET /rendez-vous/a_venir/
        Retourne les rendez-vous à venir.
        """
        rdvs = RendezVous.rdv_a_venir()
        serializer = RendezVousSerializer(rdvs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mes_rdv(self, request):
        """
        GET /rendez-vous/mes_rdv/
        Retourne les rendez-vous du citoyen connecté.
        """
        try:
            citoyen = Citoyen.objects.get(utilisateur=request.user)
        except Citoyen.DoesNotExist:
            return Response([])
        
        rdvs = RendezVous.rdv_par_citoyen(citoyen.id)
        serializer = RendezVousSerializer(rdvs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def du_jour(self, request):
        """
        GET /rendez-vous/du_jour/
        Retourne les rendez-vous du jour (pour les agents).
        """
        if not request.user.is_agent_or_admin:
            raise PermissionDenied()
        
        rdvs = RendezVous.rdv_du_jour(date.today())
        serializer = RendezVousSerializer(rdvs, many=True)
        return Response(serializer.data)
