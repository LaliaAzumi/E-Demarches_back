"""
Classes de base pour les views (MVC Controllers)
"""

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from ..permissions import IsOwnerOrReadOnly, IsAgentOrAdmin


class BaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet de base avec configuration commune.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    def get_queryset(self):
        """Par défaut, retourne tous les objets."""
        return self.queryset


class ReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet lecture seule avec configuration commune.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]


class CitoyenOwnedViewSet(BaseViewSet):
    """
    ViewSet pour ressources appartenant à un citoyen.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Filtre par citoyen connecté si ce n'est pas un agent/admin."""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_agent_or_admin:
            try:
                citoyen = user.citoyen_profile
                queryset = queryset.filter(citoyen=citoyen)
            except AttributeError:
                queryset = queryset.none()
        
        return queryset


class AgentRequiredViewSet(BaseViewSet):
    """
    ViewSet accessible uniquement aux agents et admins.
    """
    permission_classes = [IsAuthenticated, IsAgentOrAdmin]
