"""
Views pour la FAQ (MVC Controller)
"""

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.db.models import Q

from ..models import FAQChatbot
from ..serializers import FAQSerializer, FAQSearchSerializer
from .base import ReadOnlyViewSet


class FAQViewSet(ReadOnlyViewSet):
    """
    Controller pour la FAQ.
    Lecture pour tous, modifications réservées aux admins.
    """
    queryset = FAQChatbot.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    filter_backends = [filters.SearchFilter]
    filterset_fields = ['categorie']
    search_fields = ['question', 'reponse', 'mots_cles']
    
    def get_permissions(self):
        """Admins peuvent tout faire, autres uniquement lecture."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Les admins voient aussi les FAQs inactives."""
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return FAQChatbot.objects.all()
        return queryset
    
    @action(detail=True, methods=['post'])
    def utile(self, request, pk=None):
        """
        POST /faq/{id}/utile/
        Marque une FAQ comme utile.
        """
        faq = self.get_object()
        faq.marquer_utile()
        return Response({'message': 'Merci pour votre retour !'})
    
    @action(detail=True, methods=['post'])
    def inutile(self, request, pk=None):
        """
        POST /faq/{id}/inutile/
        Marque une FAQ comme inutile.
        """
        faq = self.get_object()
        faq.marquer_inutile()
        return Response({'message': 'Merci pour votre retour !'})
    
    @action(detail=True, methods=['get'])
    def voir(self, request, pk=None):
        """
        GET /faq/{id}/voir/
        Incrémente les vues d'une FAQ et la retourne.
        """
        faq = self.get_object()
        faq.incrementer_vues()
        serializer = FAQSerializer(faq)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def rechercher(self, request):
        """
        POST /faq/rechercher/
        Recherche dans la FAQ.
        """
        serializer = FAQSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query = serializer.validated_data['query']
        categorie = serializer.validated_data.get('categorie')
        
        faqs = FAQChatbot.objects.filter(is_active=True)
        
        if categorie:
            faqs = faqs.filter(categorie=categorie)
        
        # Recherche textuelle
        faqs = faqs.filter(
            Q(question__icontains=query) |
            Q(reponse__icontains=query) |
            Q(mots_cles__icontains=query)
        )
        
        serializer = FAQSerializer(faqs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        GET /faq/categories/
        Retourne les catégories disponibles.
        """
        categories = FAQChatbot.objects.filter(is_active=True).values_list(
            'categorie', flat=True
        ).distinct()
        return Response(list(filter(None, categories)))
    
    @action(detail=False, methods=['get'])
    def populaires(self, request):
        """
        GET /faq/populaires/
        Retourne les 5 FAQs les plus consultées.
        """
        faqs = FAQChatbot.objects.filter(is_active=True).order_by('-vues')[:5]
        serializer = FAQSerializer(faqs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def plus_utiles(self, request):
        """
        GET /faq/plus_utiles/
        Retourne les 5 FAQs les plus utiles.
        """
        faqs = FAQChatbot.objects.filter(is_active=True).order_by('-utile')[:5]
        serializer = FAQSerializer(faqs, many=True)
        return Response(serializer.data)
