"""
Views pour les dashboards (MVC Controller)
Endpoints dédiés aux statistiques et tableaux de bord.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from ..models import (
    DemandeAdministrative, Citoyen, AgentAdministratif,
    RendezVous, Notification
)
from ..serializers import (
    DemandeListSerializer,
    RendezVousSerializer,
    DashboardStatsSerializer,
    DashboardCitoyenSerializer,
    DashboardAgentSerializer
)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    GET /dashboard/stats/
    Statistiques globales pour le dashboard admin.
    """
    if not request.user.is_agent_or_admin:
        return Response({'error': 'Accès refusé'}, status=403)
    
    data = {
        'total_demandes': DemandeAdministrative.objects.count(),
        'demandes_en_attente': DemandeAdministrative.objects.filter(
            statut='en_attente'
        ).count(),
        'demandes_en_cours': DemandeAdministrative.objects.filter(
            statut='en_cours'
        ).count(),
        'demandes_validees': DemandeAdministrative.objects.filter(
            statut='validee'
        ).count(),
        'demandes_rejetees': DemandeAdministrative.objects.filter(
            statut='rejetee'
        ).count(),
        'total_citoyens': Citoyen.objects.count(),
        'total_agents': AgentAdministratif.objects.count(),
        'rdv_a_venir': RendezVous.rdv_a_venir().count(),
        'notifications_non_lues': Notification.non_lues(request.user.id).count(),
    }
    serializer = DashboardStatsSerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_citoyen(request):
    """
    GET /dashboard/citoyen/
    Dashboard personnalisé pour un citoyen.
    """
    try:
        citoyen = Citoyen.objects.get(utilisateur=request.user)
    except Citoyen.DoesNotExist:
        return Response({
            'error': 'Vous devez être un citoyen pour accéder à ce dashboard'
        }, status=403)
    
    mes_demandes = DemandeAdministrative.objects.filter(citoyen=citoyen)
    mes_rdv = RendezVous.rdv_par_citoyen(citoyen.id)[:5]
    
    data = {
        'mes_demandes_total': mes_demandes.count(),
        'mes_demandes_en_cours': mes_demandes.filter(
            statut__in=['en_attente', 'en_cours']
        ).count(),
        'mes_demandes_validees': mes_demandes.filter(statut='validee').count(),
        'mes_rdv': RendezVous.objects.filter(citoyen=citoyen).count(),
        'mes_notifications_non_lues': Notification.non_lues(
            request.user.id
        ).count(),
        'dernieres_demandes': DemandeListSerializer(
            mes_demandes[:5], many=True
        ).data,
        'prochains_rdv': RendezVousSerializer(mes_rdv, many=True).data,
    }
    serializer = DashboardCitoyenSerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_agent(request):
    """
    GET /dashboard/agent/
    Dashboard personnalisé pour un agent.
    """
    if not request.user.is_agent_or_admin:
        return Response({
            'error': 'Vous devez être un agent pour accéder à ce dashboard'
        }, status=403)
    
    try:
        from ..models import Traitement, PropositionRDV
        agent = AgentAdministratif.objects.get(utilisateur=request.user)
    except AgentAdministratif.DoesNotExist:
        return Response({
            'error': 'Profil agent non trouvé'
        }, status=404)
    
    data = {
        'demandes_a_traiter': DemandeAdministrative.objects.filter(
            statut='en_attente'
        ).count(),
        'mes_traitements_ce_mois': Traitement.objects.filter(
            agent=agent,
            date_traitement__month=timezone.now().month
        ).count(),
        'propositions_rdv_a_venir': PropositionRDV.objects.filter(
            agent=agent,
            statut='propose',
            date__gte=timezone.now().date()
        ).count(),
        'rdv_du_jour': RendezVous.rdv_du_jour().count(),
    }
    serializer = DashboardAgentSerializer(data)
    return Response(serializer.data)
