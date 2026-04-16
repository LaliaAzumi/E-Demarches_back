from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Demande, Traitement, PropositionRDV, RendezVous
from .serializers import (
    DemandeSerializer, DemandeCreateSerializer,
    TraitementSerializer, PropositionRDVSerializer, RendezVousSerializer
)
from apps.users.models import Citoyen, Agent
from apps.users.permissions import IsAgent, IsCitoyen


class DemandeViewSet(viewsets.ModelViewSet):
    queryset = Demande.objects.all().select_related('citoyen', 'citoyen__utilisateur').prefetch_related('traitements', 'propositions_rdv')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return DemandeCreateSerializer
        return DemandeSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'agent':
            return Demande.objects.all()
        else:
            try:
                citoyen = Citoyen.objects.get(utilisateur=user)
                return Demande.objects.filter(citoyen=citoyen)
            except Citoyen.DoesNotExist:
                return Demande.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role == 'citoyen':
            citoyen = Citoyen.objects.get(utilisateur=self.request.user)
            serializer.save(citoyen=citoyen)
        else:
            serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[IsAgent])
    def traiter(self, request, pk=None):
        demande = self.get_object()
        commentaire = request.data.get('commentaire')
        nouveau_statut = request.data.get('statut')
        try:
            agent = Agent.objects.get(utilisateur=request.user)
        except Agent.DoesNotExist:
            return Response({'error': 'Agent non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        traitement = Traitement.objects.create(
            demande=demande, agent=agent,
            commentaire=commentaire,
            statut_apres_traitement=nouveau_statut
        )
        if nouveau_statut:
            demande.statut = nouveau_statut
            demande.save()
        return Response(TraitementSerializer(traitement).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAgent])
    def proposer_rdv(self, request, pk=None):
        demande = self.get_object()
        date = request.data.get('date')
        heure = request.data.get('heure')
        if not date or not heure:
            return Response({'error': 'Date et heure requises'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            agent = Agent.objects.get(utilisateur=request.user)
        except Agent.DoesNotExist:
            return Response({'error': 'Agent non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        proposition = PropositionRDV.objects.create(
            demande=demande, agent=agent, date=date, heure=heure
        )
        return Response(PropositionRDVSerializer(proposition).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsCitoyen])
    def choisir_rdv(self, request, pk=None):
        demande = self.get_object()
        proposition_id = request.data.get('proposition_id')
        try:
            citoyen = Citoyen.objects.get(utilisateur=request.user)
        except Citoyen.DoesNotExist:
            return Response({'error': 'Citoyen non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        try:
            proposition = PropositionRDV.objects.get(id=proposition_id, demande=demande, statut='propose')
        except PropositionRDV.DoesNotExist:
            return Response({'error': 'Proposition non trouvée'}, status=status.HTTP_404_NOT_FOUND)

        proposition.statut = 'choisi'
        proposition.save()
        rdv = RendezVous.objects.create(proposition=proposition, citoyen=citoyen)
        return Response(RendezVousSerializer(rdv).data, status=status.HTTP_201_CREATED)


class TraitementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Traitement.objects.all().select_related('demande', 'agent', 'agent__utilisateur')
    serializer_class = TraitementSerializer
    permission_classes = [IsAuthenticated]


class PropositionRDVViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PropositionRDV.objects.all().select_related('demande', 'agent', 'agent__utilisateur')
    serializer_class = PropositionRDVSerializer
    permission_classes = [IsAuthenticated]


class RendezVousViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RendezVous.objects.all().select_related('proposition', 'proposition__demande', 'citoyen', 'citoyen__utilisateur')
    serializer_class = RendezVousSerializer
    permission_classes = [IsAuthenticated]
