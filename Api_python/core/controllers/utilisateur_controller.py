"""
Views pour la gestion des utilisateurs (MVC Controller)
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response

from ..models import Utilisateur, Citoyen
from ..serializers import (
    UtilisateurSerializer, 
    UtilisateurCreateSerializer, 
    LoginSerializer
)


class UtilisateurViewSet(viewsets.ModelViewSet):
    """
    Controller pour gérer les utilisateurs.
    Endpoints: register, login, me, list, CRUD
    """
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['email', 'nom', 'prenom', 'telephone']
    
    def get_serializer_class(self):
        """Sélectionne le serializer selon l'action."""
        if self.action == 'create':
            return UtilisateurCreateSerializer
        return UtilisateurSerializer
    
    def get_permissions(self):
        """Permissions dynamiques selon l'action."""
        if self.action in ['create', 'register', 'login']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        POST /utilisateurs/register/
        Inscription d'un nouvel utilisateur citoyen.
        """
        serializer = UtilisateurCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Créer le profil citoyen associé
        Citoyen.objects.create(utilisateur=user)
        
        return Response({
            'message': 'Utilisateur créé avec succès',
            'user': UtilisateurSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        POST /utilisateurs/login/
        Connexion et génération de token JWT.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        
        # Générer token JWT
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UtilisateurSerializer(user).data
        })
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        GET /utilisateurs/me/
        Retourne l'utilisateur connecté.
        """
        return Response(UtilisateurSerializer(request.user).data)
    
    @action(detail=False, methods=['get'])
    def citoyens(self, request):
        """
        GET /utilisateurs/citoyens/
        Liste tous les citoyens.
        """
        citoyens = Utilisateur.objects.filter(role='citoyen')
        serializer = self.get_serializer(citoyens, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def agents(self, request):
        """
        GET /utilisateurs/agents/
        Liste tous les agents (admin uniquement).
        """
        if not request.user.is_agent_or_admin:
            return Response({'error': 'Accès refusé'}, status=403)
        
        agents = Utilisateur.objects.filter(role='agent')
        serializer = self.get_serializer(agents, many=True)
        return Response(serializer.data)
