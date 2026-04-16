from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from allauth.account.models import EmailAddress
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import Utilisateur, Citoyen, Agent
from .serializers import (
    UtilisateurSerializer, UtilisateurCreateSerializer,
    CitoyenSerializer, AgentSerializer
)
from .permissions import IsAgent
import logging

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    """Génère les tokens JWT pour un utilisateur"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class UtilisateurViewSet(viewsets.ModelViewSet):
    queryset = Utilisateur.objects.all()
    serializer_class = UtilisateurSerializer

    def get_permissions(self):
        if self.action in ['create', 'login', 'register']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UtilisateurCreateSerializer
        return UtilisateurSerializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        POST /api/users/register/
        Inscription d'un nouvel utilisateur avec envoi d'email de confirmation
        """
        serializer = UtilisateurCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Créer le profil Citoyen automatiquement
            Citoyen.objects.create(
                utilisateur=user,
                prenom=request.data.get('prenom', ''),
                date_naissance=request.data.get('date_naissance') or None,
                cin=request.data.get('cin') or None,
                adresse=request.data.get('adresse', ''),
            )
            
            # Créer l'objet EmailAddress pour allauth
            email_address = EmailAddress.objects.create(
                user=user,
                email=user.email,
                primary=True,
                verified=False
            )
            
            # Envoyer l'email de confirmation
            try:
                email_address.send_confirmation(request)
            except Exception as e:
                logger.warning(f"Erreur envoi email confirmation: {e}")
            
            tokens = get_tokens_for_user(user)
            return Response({
                'user': UtilisateurSerializer(user).data,
                'tokens': tokens,
                'message': 'Inscription réussie. Veuillez confirmer votre email.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        POST /api/users/login/
        Connexion avec JWT tokens
        """
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email et mot de passe requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, email=email, password=password)
        
        if user:
            # Vérifier si l'email est confirmé
            try:
                email_address = EmailAddress.objects.get(user=user, primary=True)
                if not email_address.verified:
                    return Response({
                        'error': 'Email non confirmé',
                        'message': 'Veuillez confirmer votre email avant de vous connecter.',
                        'email_verified': False
                    }, status=status.HTTP_403_FORBIDDEN)
            except EmailAddress.DoesNotExist:
                pass
            
            login(request, user)
            tokens = get_tokens_for_user(user)
            
            data = {
                'user': UtilisateurSerializer(user).data,
                'tokens': tokens,
                'email_verified': True
            }
            
            # Ajouter le profil citoyen/agent
            if user.role == 'citoyen':
                try:
                    citoyen = Citoyen.objects.get(utilisateur=user)
                    data['citoyen'] = CitoyenSerializer(citoyen).data
                except Citoyen.DoesNotExist:
                    data['citoyen'] = None
            elif user.role == 'agent':
                try:
                    agent = Agent.objects.get(utilisateur=user)
                    data['agent'] = AgentSerializer(agent).data
                except Agent.DoesNotExist:
                    data['agent'] = None
            
            return Response(data)
        
        return Response(
            {'error': 'Email ou mot de passe incorrect'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        POST /api/users/logout/
        Déconnexion (blacklist le refresh token si fourni)
        """
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception as e:
            logger.warning(f"Erreur lors du blacklist du token: {e}")
        
        logout(request)
        return Response({'message': 'Déconnexion réussie'})

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        GET /api/users/me/
        Récupère les informations de l'utilisateur connecté (avec profil citoyen/agent)
        """
        serializer = UtilisateurSerializer(request.user)
        
        # Vérifier le statut de vérification de l'email
        try:
            email_address = EmailAddress.objects.get(user=request.user, primary=True)
            email_verified = email_address.verified
        except EmailAddress.DoesNotExist:
            email_verified = False
        
        data = {
            'user': serializer.data,
            'email_verified': email_verified
        }
        
        # Ajouter le profil citoyen si applicable
        if request.user.role == 'citoyen':
            try:
                citoyen = Citoyen.objects.get(utilisateur=request.user)
                data['citoyen'] = CitoyenSerializer(citoyen).data
            except Citoyen.DoesNotExist:
                data['citoyen'] = None
        elif request.user.role == 'agent':
            try:
                agent = Agent.objects.get(utilisateur=request.user)
                data['agent'] = AgentSerializer(agent).data
            except Agent.DoesNotExist:
                data['agent'] = None
        
        return Response(data)

    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """
        PATCH /api/users/update_profile/
        Met à jour les informations du profil utilisateur + citoyen
        """
        user = request.user
        
        # Mettre à jour les champs Utilisateur
        user_fields = ['nom']
        for field in user_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        
        # Mettre à jour le profil Citoyen si applicable
        citoyen_data = {}
        citoyen_fields = ['prenom', 'date_naissance', 'cin', 'adresse']
        for field in citoyen_fields:
            if field in request.data:
                citoyen_data[field] = request.data[field] or None
        
        if citoyen_data and user.role == 'citoyen':
            try:
                citoyen = Citoyen.objects.get(utilisateur=user)
                for field, value in citoyen_data.items():
                    setattr(citoyen, field, value)
                citoyen.save()
            except Citoyen.DoesNotExist:
                Citoyen.objects.create(utilisateur=user, **citoyen_data)
        
        
        # Retourner les données mises à jour
        return self.me(request)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def check_email_verified(self, request):
        """
        GET /api/users/check_email_verified/?email=...
        Vérifie si l'email d'un utilisateur est vérifié
        """
        email = request.query_params.get('email')
        if not email:
            return Response({'error': 'Email requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            email_address = EmailAddress.objects.get(email=email, primary=True)
            return Response({
                'email': email,
                'verified': email_address.verified
            })
        except EmailAddress.DoesNotExist:
            return Response({
                'email': email,
                'verified': False
            })

    @action(detail=False, methods=['post'])
    def refresh_token(self, request):
        """
        POST /api/users/refresh-token/
        Rafraîchit le token d'accès
        """
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            })
        except Exception:
            return Response(
                {'error': 'Refresh token invalide'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def password_reset_request(self, request):
        """
        POST /api/users/password-reset-request/
        Demande de réinitialisation de mot de passe
        """
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = Utilisateur.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
            
            send_mail(
                subject='Réinitialisation de votre mot de passe',
                message=f'Cliquez sur ce lien pour réinitialiser votre mot de passe : {reset_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Utilisateur.DoesNotExist:
            # Ne pas révéler si l'email existe ou non (sécurité)
            pass
        
        return Response({
            'message': 'Si cet email existe, un lien de réinitialisation a été envoyé.'
        })

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def password_reset_confirm(self, request):
        """
        POST /api/users/password-reset-confirm/
        Confirmation de réinitialisation de mot de passe
        """
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not all([uid, token, new_password]):
            return Response(
                {'error': 'Tous les champs sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = Utilisateur.objects.get(pk=uid)
            
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Mot de passe réinitialisé avec succès'})
            else:
                return Response(
                    {'error': 'Token invalide ou expiré'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (Utilisateur.DoesNotExist, ValueError, TypeError):
            return Response(
                {'error': 'Lien invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def resend_verification_email(self, request):
        """
        POST /api/users/resend_verification_email/
        Renvoyer l'email de confirmation (accessible sans auth)
        """
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            email_address = EmailAddress.objects.get(email=email, primary=True)
            if email_address.verified:
                return Response(
                    {'message': 'Email déjà vérifié'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            email_address.send_confirmation(request)
            return Response({'message': 'Email de confirmation envoyé'})
        except EmailAddress.DoesNotExist:
            return Response(
                {'error': 'Adresse email non trouvée'},
                status=status.HTTP_400_BAD_REQUEST
            )



@api_view(['POST'])
@permission_classes([AllowAny])
def google_login_verify(request):
    """
    POST /api/users/google-login/
    Vérifie le credential Google (ID token) envoyé par le frontend,
    crée ou connecte l'utilisateur, et renvoie les tokens JWT.
    """
    credential = request.data.get('credential')
    if not credential:
        return Response(
            {'error': 'Credential Google requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
        )
    except ValueError as e:
        logger.warning(f"Google token verification failed: {e}")
        return Response(
            {'error': 'Token Google invalide'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    email = idinfo.get('email')
    name = idinfo.get('name', '')
    if not email:
        return Response(
            {'error': 'Email non fourni par Google'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Créer ou récupérer l'utilisateur
    try:
        user = Utilisateur.objects.get(email=email)
    except Utilisateur.DoesNotExist:
        user = Utilisateur.objects.create_user(
            email=email,
            nom=name,
            mot_de_passe=None,
            role='citoyen',
        )
        Citoyen.objects.create(utilisateur=user)

        # Marquer l'email comme vérifié (Google l'a déjà vérifié)
        EmailAddress.objects.create(
            user=user,
            email=email,
            primary=True,
            verified=True
        )

    # Vérifier/marquer l'email comme vérifié si pas encore fait
    try:
        email_address = EmailAddress.objects.get(user=user, primary=True)
        if not email_address.verified:
            email_address.verified = True
            email_address.save()
    except EmailAddress.DoesNotExist:
        EmailAddress.objects.create(
            user=user,
            email=email,
            primary=True,
            verified=True
        )

    login(request, user)
    tokens = get_tokens_for_user(user)
    return Response({
        'user': UtilisateurSerializer(user).data,
        'tokens': tokens,
        'email_verified': True
    })


class CitoyenViewSet(viewsets.ModelViewSet):
    queryset = Citoyen.objects.all().select_related('utilisateur')
    serializer_class = CitoyenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'agent':
            return Citoyen.objects.all()
        return Citoyen.objects.filter(utilisateur=user)


class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all().select_related('utilisateur')
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'agent':
            return Agent.objects.all()
        return Agent.objects.filter(utilisateur=user)
