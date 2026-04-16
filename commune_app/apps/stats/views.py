from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Statistique
from .serializers import StatistiqueSerializer, StatistiqueGlobaleSerializer
from apps.users.models import Utilisateur
from apps.dossiers.models import Demande, Traitement
from apps.documents.models import Document
from apps.users.permissions import IsAgent


class StatistiqueViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], permission_classes=[IsAgent])
    def globale(self, request):
        total_demandes = Demande.objects.count()
        demandes_par_statut = dict(Demande.objects.values('statut').annotate(count=Count('id')).values_list('statut', 'count'))
        demandes_par_type = dict(Demande.objects.values('type_demande').annotate(count=Count('id')).values_list('type_demande', 'count'))

        total_utilisateurs = Utilisateur.objects.count()
        utilisateurs_par_role = dict(Utilisateur.objects.values('role').annotate(count=Count('id')).values_list('role', 'count'))

        total_documents = Document.objects.count()
        total_traitements = Traitement.objects.count()

        data = {
            'total_demandes': total_demandes,
            'demandes_par_statut': demandes_par_statut,
            'demandes_par_type': demandes_par_type,
            'total_utilisateurs': total_utilisateurs,
            'utilisateurs_par_role': utilisateurs_par_role,
            'total_documents': total_documents,
            'total_traitements': total_traitements,
        }

        serializer = StatistiqueGlobaleSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def demandes_temps(self, request):
        jours = int(request.query_params.get('jours', 30))
        date_debut = timezone.now() - timedelta(days=jours)

        stats = Demande.objects.filter(
            date_demande__gte=date_debut
        ).extra(
            select={'date': 'date(date_demande)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        return Response(list(stats))

    @action(detail=False, methods=['get'])
    def activite_recente(self, request):
        jours = int(request.query_params.get('jours', 7))
        date_debut = timezone.now() - timedelta(days=jours)

        traitements = Traitement.objects.filter(
            date_traitement__gte=date_debut
        ).count()

        nouvelles_demandes = Demande.objects.filter(
            date_demande__gte=date_debut
        ).count()

        nouveaux_documents = Document.objects.filter(
            date_upload__gte=date_debut
        ).count()

        return Response({
            'traitements': traitements,
            'nouvelles_demandes': nouvelles_demandes,
            'nouveaux_documents': nouveaux_documents,
            'periode_jours': jours
        })


class StatistiqueCRUDViewSet(viewsets.ModelViewSet):
    queryset = Statistique.objects.all()
    serializer_class = StatistiqueSerializer
    permission_classes = [IsAgent]
