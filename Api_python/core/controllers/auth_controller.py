"""
Controller pour l'authentification OAuth (Google)
"""

import requests
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from ..models import Utilisateur, Citoyen
from ..serializers import (
    UtilisateurSerializer, 
    GoogleAuthSerializer,
)


class GoogleAuthViewSet(viewsets.ViewSet):
    """
    ViewSet pour l'authentification Google OAuth.
    """
    permission_classes = [AllowAny]
    serializer_class = GoogleAuthSerializer
    
    @action(detail=False, methods=['post'], url_path='login')
    def google_login(self, request):
        """
        POST /auth/google/login/
        Authentifie un utilisateur via Google OAuth.
        
        Body:
            - access_token: Token d'accès Google
            
        Returns:
            - access: JWT access token
            - refresh: JWT refresh token
            - user: Données utilisateur
        """
        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        access_token = serializer.validated_data['access_token']
        
        # Vérifier le token avec Google
        google_user_info = self._verify_google_token(access_token)
        
        if not google_user_info:
            return Response(
                {'success': False, 'message': 'Token Google invalide'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        email = google_user_info.get('email')
        google_id = google_user_info.get('sub') or google_user_info.get('id')
        first_name = google_user_info.get('given_name', '')
        last_name = google_user_info.get('family_name', '')
        picture = google_user_info.get('picture', '')
        
        if not email:
            return Response(
                {'success': False, 'message': 'Email non fourni par Google'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Chercher ou créer l'utilisateur
        try:
            user = Utilisateur.objects.get(email__iexact=email)
            is_new_user = False
            
            # Mettre à jour les infos Google si nécessaire
            if not user.auth_provider:
                user.auth_provider = 'google'
                user.social_id = google_id
                user.avatar_url = picture or user.avatar_url
                user.save()
                
        except Utilisateur.DoesNotExist:
            # Créer nouvel utilisateur
            is_new_user = True
            user = self._create_google_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                google_id=google_id,
                picture=picture
            )
        
        # Générer tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Connexion réussie',
            'is_new_user': is_new_user,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UtilisateurSerializer(user).data
        })
    
    @action(detail=False, methods=['post'], url_path='verify')
    def verify_token(self, request):
        """
        POST /auth/google/verify/
        Vérifie un token Google sans créer de session.
        """
        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        access_token = serializer.validated_data['access_token']
        user_info = self._verify_google_token(access_token)
        
        if not user_info:
            return Response(
                {'success': False, 'message': 'Token invalide'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return Response({
            'success': True,
            'data': {
                'email': user_info.get('email'),
                'verified': user_info.get('verified_email', False),
                'name': user_info.get('name'),
                'picture': user_info.get('picture')
            }
        })
    
    def _verify_google_token(self, access_token):
        """
        Vérifie le token d'accès Google avec l'API Google.
        """
        try:
            # Vérifier avec Google UserInfo endpoint
            response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code == 200:
                return response.json()
            
            # Fallback sur l'ancien endpoint
            response = requests.get(
                'https://www.googleapis.com/oauth2/v1/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                params={'alt': 'json'}
            )
            
            if response.status_code == 200:
                return response.json()
                
            return None
            
        except requests.RequestException:
            return None
    
    def _create_google_user(self, email, first_name, last_name, google_id, picture):
        """
        Crée un nouvel utilisateur à partir des données Google.
        """
        import secrets
        # Generate a random password for OAuth users (they won't use it)
        random_password = secrets.token_urlsafe(32)
        
        user = Utilisateur.objects.create_user(
            email=email.lower().strip(),
            nom=last_name or 'Utilisateur',
            prenom=first_name or 'Google',
            telephone='',
            password=random_password,
            role='citoyen'
        )
        
        # Mark password as unusable since they login via OAuth
        user.set_unusable_password()
        user.auth_provider = 'google'
        user.social_id = google_id
        user.avatar_url = picture or ''
        user.save()
        
        # Créer le profil citoyen
        Citoyen.objects.create(utilisateur=user)
        
        return user


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet général pour l'authentification (JWT refresh, logout, etc.)
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh_token(self, request):
        """
        POST /auth/refresh/
        Rafraîchit le token JWT.
        """
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'success': False, 'message': 'Refresh token manquant'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh['user_id']
            user = Utilisateur.objects.get(id=user_id)
            
            # Générer nouveau token
            new_refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'access': str(new_refresh.access_token),
                'refresh': str(new_refresh)
            })
            
        except Exception:
            return Response(
                {'success': False, 'message': 'Token invalide ou expiré'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        """
        POST /auth/logout/
        Déconnexion (blacklist le refresh token si configuré).
        """
        # Ici vous pouvez ajouter le blacklist de token si django-rest-framework-simplejwt 
        # est configuré avec ROTATE_REFRESH_TOKENS et BLACKLIST_AFTER_ROTATION
        return Response({
            'success': True,
            'message': 'Déconnexion réussie'
        })
    
    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        GET /auth/me/
        Retourne l'utilisateur connecté.
        """
        serializer = UtilisateurSerializer(request.user)
        return Response({
            'success': True,
            'user': serializer.data
        })
