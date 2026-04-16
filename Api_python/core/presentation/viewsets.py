"""
================================================================================
MODULE: viewsets.py
COUCHE: Presentation
RÔLE: ViewSets DRF - Points d'entrée API REST

ARCHITECTURE:
    Les ViewSets exposent les fonctionnalités via HTTP/REST.
    Ils utilisent les Services (Application Layer) pour le traitement.

    AuthViewSet: /auth/ - Login, register, refresh, logout
    UtilisateurViewSet: /utilisateurs/ - Profils utilisateurs
    DemandeViewSet: /demandes/ - Gestion demandes
    DocumentViewSet: /documents/ - Upload et gestion documents
    NotificationViewSet: /notifications/ - Notifications

PATTERN: ModelViewSet (Django REST Framework)
AGILE: ViewSets = REST API pour chaque User Story
================================================================================
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import Http404

from ..domain.exceptions import (
    DomainException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
    AuthenticationException,
    BusinessRuleException
)
from ..application.services import (
    AuthService,
    DemandeService,
    NotificationService,
    RDVService,
    DocumentService
)
from .permissions import (
    IsCitoyen,
    IsAgent,
    IsAdministrateur,
    IsOwnerOrAdmin,
    CanAccessDemande,
    CanModifyDemande,
    CanCreateDemande
)
from .serializers import (
    # Auth
    RegisterSerializer,
    LoginSerializer,
    OAuthSerializer,
    RefreshTokenSerializer,
    AuthResponseSerializer,
    # User
    UtilisateurSerializer,
    ChangePasswordSerializer,
    # Demande
    CreateDemandeSerializer,
    UpdateDemandeSerializer,
    DemandeSerializer,
    DemandeListSerializer,
    StatusChangeSerializer,
    AssignDemandeSerializer,
    # Document
    UploadDocumentSerializer,
    DocumentSerializer,
    # Notification
    NotificationSerializer,
    # Pagination
    PaginationSerializer,
    ErrorResponseSerializer
)


# ============================================================================
# CLASSE BASE AVEC GESTION D'EXCEPTIONS
# ============================================================================

class ExceptionHandlerMixin:
    """
    Mixin pour la gestion centralisée des exceptions.
    
    CONVERTIT:
        - DomainException → Réponse HTTP 400/403/404
        - Exception inattendue → Réponse HTTP 500
    
    UTILISATION:
        >>> class MyViewSet(ExceptionHandlerMixin, viewsets.ViewSet):
        ...     @handle_exceptions
        ...     def my_action(self, request):
        ...         # Exceptions gérées automatiquement
    """
    
    def handle_exception(self, exc):
        """
        Gestionnaire d'exceptions personnalisé.
        
        PARAMÈTRES:
            exc: Exception levée
            
        RETOURNE:
            Response avec statut HTTP approprié
        """
        # Domain exceptions
        if isinstance(exc, ValidationException):
            return Response({
                'success': False,
                'error': {
                    'code': exc.code.value,
                    'message': exc.message,
                    'field': exc.field,
                    'details': exc.details
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if isinstance(exc, NotFoundException):
            return Response({
                'success': False,
                'error': {
                    'code': exc.code.value,
                    'message': exc.message,
                    'details': exc.details
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        if isinstance(exc, PermissionDeniedException):
            return Response({
                'success': False,
                'error': {
                    'code': exc.code.value,
                    'message': exc.message,
                    'details': exc.details
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        if isinstance(exc, AuthenticationException):
            return Response({
                'success': False,
                'error': {
                    'code': exc.code.value,
                    'message': exc.message,
                    'details': exc.details
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if isinstance(exc, BusinessRuleException):
            return Response({
                'success': False,
                'error': {
                    'code': exc.code.value,
                    'message': exc.message,
                    'details': exc.details
                }
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        # Django 404
        if isinstance(exc, Http404):
            return Response({
                'success': False,
                'error': {
                    'code': 'ERR_1002',
                    'message': 'Ressource non trouvée'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Exception inattendue (en production, logger et retourner générique)
        # TODO: Ajouter logging ici
        return Response({
            'success': False,
            'error': {
                'code': 'ERR_1000',
                'message': 'Une erreur inattendue est survenue'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# VIEWSET AUTHENTIFICATION
# ============================================================================

class AuthViewSet(ExceptionHandlerMixin, viewsets.ViewSet):
    """
    ViewSet pour l'authentification.
    
    ENDPOINTS:
        POST /auth/register/ - Inscription
        POST /auth/login/ - Connexion email/password
        POST /auth/oauth/ - Connexion OAuth
        POST /auth/refresh/ - Rafraîchir token
        POST /auth/logout/ - Déconnexion
        GET /auth/me/ - Profil connecté
        POST /auth/change-password/ - Changer mot de passe
    
    PERMISSIONS:
        - register, login, oauth: AllowAny
        - Autres: IsAuthenticated
    
    EXEMPLE:
        >>> POST /api/auth/register/
        >>> {
        ...     "email": "test@example.com",
        ...     "password": "SecurePass123",
        ...     "password_confirm": "SecurePass123",
        ...     "nom": "DIOP",
        ...     "prenom": "Amadou"
        ... }
    """
    
    def get_permissions(self):
        """Définit les permissions selon l'action."""
        if self.action in ['register', 'login', 'oauth']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Injecter le service (normalement via DI)
        self.auth_service = None  # À injecter
    
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request: Request):
        """
        Inscription d'un nouvel utilisateur.
        
        BODY:
            RegisterSerializer fields
            
        RESPONSE:
            AuthResponseSerializer
        """
        serializer = RegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        dto = serializer.to_dto()
        result = self.auth_service.register(dto)
        
        if result.success:
            return Response({
                'success': True,
                'message': result.message,
                'access_token': result.access_token,
                'refresh_token': result.refresh_token,
                'user': self._user_to_dict(result.user),
                'is_new_user': result.is_new_user
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': result.message,
            'errors': result.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request: Request):
        """
        Connexion avec email/password.
        
        BODY:
            - email: string
            - password: string
            
        RESPONSE:
            AuthResponseSerializer
        """
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        dto = serializer.to_dto()
        
        try:
            result = self.auth_service.login(dto)
            
            return Response({
                'success': True,
                'message': result.message,
                'access_token': result.access_token,
                'refresh_token': result.refresh_token,
                'user': self._user_to_dict(result.user)
            })
        except AuthenticationException as e:
            return self.handle_exception(e)
    
    @action(detail=False, methods=['post'], url_path='oauth')
    def oauth(self, request: Request):
        """
        Connexion via OAuth (Google, Facebook).
        
        BODY:
            - provider: 'google' | 'facebook'
            - access_token: string
            
        RESPONSE:
            AuthResponseSerializer
        """
        serializer = OAuthSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        dto = serializer.to_dto()
        result = self.auth_service.oauth_login(dto)
        
        if result.success:
            return Response({
                'success': True,
                'message': result.message,
                'access_token': result.access_token,
                'refresh_token': result.refresh_token,
                'user': self._user_to_dict(result.user),
                'is_new_user': result.is_new_user
            })
        
        return Response({
            'success': False,
            'message': result.message
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh(self, request: Request):
        """
        Rafraîchit les tokens d'accès.
        
        BODY:
            - refresh_token: string
            
        RESPONSE:
            - access_token: string
            - refresh_token: string
        """
        serializer = RefreshTokenSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        refresh_token = serializer.validated_data['refresh_token']
        result = self.auth_service.refresh_token(refresh_token)
        
        if result.success:
            return Response({
                'success': True,
                'access_token': result.access_token,
                'refresh_token': result.refresh_token
            })
        
        return Response({
            'success': False,
            'message': result.message
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request: Request):
        """
        Déconnexion (blacklist le refresh token).
        
        AUTHENTICATION: Required
        
        RESPONSE:
            - success: true
            - message: "Déconnexion réussie"
        """
        # TODO: Blacklist le refresh token si configuré
        return Response({
            'success': True,
            'message': 'Déconnexion réussie'
        })
    
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request: Request):
        """
        Retourne le profil de l'utilisateur connecté.
        
        AUTHENTICATION: Required
        
        RESPONSE:
            UtilisateurSerializer
        """
        user = request.user
        return Response({
            'success': True,
            'user': self._user_to_dict(user)
        })
    
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request: Request):
        """
        Change le mot de passe de l'utilisateur connecté.
        
        AUTHENTICATION: Required
        
        BODY:
            ChangePasswordSerializer fields
        """
        serializer = ChangePasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from ..application.dtos import ChangePasswordInputDTO
        dto = ChangePasswordInputDTO(
            current_password=serializer.validated_data['current_password'],
            new_password=serializer.validated_data['new_password'],
            new_password_confirm=serializer.validated_data['new_password_confirm']
        )
        
        result = self.auth_service.change_password(request.user.id, dto)
        
        return Response({
            'success': result.success,
            'message': result.message
        })
    
    def _user_to_dict(self, user) -> dict:
        """Convertit un utilisateur en dictionnaire."""
        return {
            'id': user.id,
            'email': user.email,
            'nom': user.nom,
            'prenom': user.prenom,
            'telephone': user.telephone,
            'role': user.role,
            'role_display': getattr(user, 'role_display', user.role),
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'avatar_url': user.avatar_url,
            'nom_complet': getattr(user, 'nom_complet', f"{user.prenom} {user.nom}")
        }


# ============================================================================
# VIEWSET UTILISATEURS
# ============================================================================

class UtilisateurViewSet(ExceptionHandlerMixin, viewsets.ViewSet):
    """
    ViewSet pour la gestion des utilisateurs.
    
    ENDPOINTS:
        GET /utilisateurs/ - Liste (admin seulement)
        GET /utilisateurs/{id}/ - Détail
        PUT /utilisateurs/{id}/ - Modifier profil
        DELETE /utilisateurs/{id}/ - Désactiver compte
        GET /utilisateurs/{id}/demandes/ - Demandes du citoyen
    
    PERMISSIONS:
        - Liste: Admin seulement
        - Détail/Update/Delete: Owner ou Admin
    """
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_service = None  # À injecter
    
    def list(self, request: Request):
        """
        Liste des utilisateurs (admin seulement).
        
        QUERY PARAMS:
            - role: filtrer par rôle
            - search: recherche textuelle
            - page, page_size: pagination
        """
        # Vérifier admin
        if not self._is_admin(request.user):
            return Response({
                'success': False,
                'error': {'message': 'Accès réservé aux administrateurs'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        # TODO: Implémenter la liste avec pagination
        return Response({
            'success': True,
            'items': [],
            'total': 0
        })
    
    def retrieve(self, request: Request, pk: int):
        """
        Détail d'un utilisateur.
        
        ACCESS: Owner ou Admin
        """
        # Vérifier accès
        if not self._can_access(request.user, pk):
            return Response({
                'success': False,
                'error': {'message': 'Accès non autorisé'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        # TODO: Récupérer l'utilisateur
        return Response({
            'success': True
        })
    
    def update(self, request: Request, pk: int):
        """
        Modification du profil.
        
        ACCESS: Owner ou Admin
        
        BODY:
            UtilisateurSerializer (partiel)
        """
        if not self._can_access(request.user, pk):
            return Response({
                'success': False,
                'error': {'message': 'Accès non autorisé'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        # TODO: Implémenter update
        return Response({
            'success': True,
            'message': 'Profil mis à jour'
        })
    
    @action(detail=True, methods=['get'], url_path='demandes')
    def demandes(self, request: Request, pk: int):
        """
        Liste les demandes d'un citoyen.
        
        ACCESS: Owner ou Admin
        """
        if not self._can_access(request.user, pk):
            return Response({
                'success': False,
                'error': {'message': 'Accès non autorisé'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        # TODO: Récupérer les demandes
        return Response({
            'success': True,
            'items': []
        })
    
    def _is_admin(self, user) -> bool:
        """Vérifie si l'utilisateur est admin."""
        return getattr(user, 'role', None) == 'administrateur'
    
    def _can_access(self, user, target_user_id: int) -> bool:
        """Vérifie si l'utilisateur peut accéder aux données d'un autre."""
        if self._is_admin(user):
            return True
        return user.id == target_user_id


# ============================================================================
# VIEWSET DEMANDES
# ============================================================================

class DemandeViewSet(ExceptionHandlerMixin, viewsets.ViewSet):
    """
    ViewSet pour la gestion des demandes administratives.
    
    ENDPOINTS:
        GET /demandes/ - Liste (filtrée selon rôle)
        POST /demandes/ - Créer (citoyen)
        GET /demandes/{id}/ - Détail
        PUT /demandes/{id}/ - Modifier (brouillon uniquement)
        DELETE /demandes/{id}/ - Supprimer (brouillon)
        
        POST /demandes/{id}/soumettre/ - Soumettre (citoyen)
        POST /demandes/{id}/assigner/ - Assigner agent (admin)
        POST /demandes/{id}/changer-statut/ - Changer statut
        GET /demandes/{id}/documents/ - Documents de la demande
        POST /demandes/{id}/documents/ - Ajouter document
        GET /demandes/statistiques/ - Stats (admin)
    
    PERMISSIONS:
        - Create: Citoyen uniquement
        - Read: Owner, Assigned Agent, ou Admin
        - Update: Owner (brouillon) ou Agent/Admin
        - Actions: Selon workflow et rôle
    """
    
    permission_classes = [IsAuthenticated, CanAccessDemande]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.demande_service = None  # À injecter
    
    def get_permissions(self):
        """Permissions dynamiques selon l'action."""
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateDemande()]
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), CanModifyDemande()]
        return [IsAuthenticated(), CanAccessDemande()]
    
    def list(self, request: Request):
        """
        Liste les demandes accessibles à l'utilisateur.
        
        FILTRAGE:
            - Citoyen: ses propres demandes
            - Agent: les demandes assignées
            - Admin: toutes les demandes
        
        QUERY PARAMS:
            - status: filtrer par statut
            - page, page_size: pagination
            
        RESPONSE:
            Paginated list de DemandeListSerializer
        """
        # Pagination
        paginator = PaginationSerializer(data=request.query_params)
        paginator.is_valid(raise_exception=True)
        pagination_dto = paginator.to_dto()
        
        # Liste selon rôle
        if request.user.role == 'citoyen':
            result = self.demande_service.list_by_citoyen(
                request.user.id,
                pagination_dto
            )
        elif request.user.role == 'agent':
            result = self.demande_service.list_by_agent(
                request.user.id,
                pagination_dto
            )
        else:  # admin
            # TODO: Liste admin avec filtres
            result = None
        
        return Response({
            'success': True,
            'items': [],  # Sérialiser les items
            'total': result.total if result else 0,
            'page': result.page if result else 1,
            'page_size': result.page_size if result else 20,
            'total_pages': result.total_pages if result else 1,
            'has_next': result.has_next if result else False,
            'has_previous': result.has_previous if result else False
        })
    
    def create(self, request: Request):
        """
        Crée une nouvelle demande (brouillon).
        
        BODY:
            CreateDemandeSerializer
            
        RESPONSE:
            DemandeSerializer (201 Created)
        """
        serializer = CreateDemandeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        dto = serializer.to_dto()
        
        try:
            result = self.demande_service.create(request.user.id, dto)
            return Response({
                'success': True,
                'message': 'Demande créée avec succès',
                'demande': self._demande_to_dict(result)
            }, status=status.HTTP_201_CREATED)
        except DomainException as e:
            return self.handle_exception(e)
    
    def retrieve(self, request: Request, pk: int):
        """
        Détail d'une demande.
        
        ACCESS: Owner, Assigned Agent, ou Admin
        
        RESPONSE:
            DemandeSerializer
        """
        try:
            result = self.demande_service.get_by_id(pk, request.user.id)
            return Response({
                'success': True,
                'demande': self._demande_to_dict(result)
            })
        except DomainException as e:
            return self.handle_exception(e)
    
    def update(self, request: Request, pk: int):
        """
        Modifie une demande (brouillon uniquement pour citoyens).
        
        BODY:
            UpdateDemandeSerializer
        """
        serializer = UpdateDemandeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # TODO: Implémenter update
        return Response({
            'success': True,
            'message': 'Demande mise à jour'
        })
    
    @action(detail=True, methods=['post'], url_path='soumettre')
    def soumettre(self, request: Request, pk: int):
        """
        Soumet une demande pour traitement.
        
        TRANSITION: brouillon → soumise
        
        ACCESS: Citoyen propriétaire
        """
        try:
            result = self.demande_service.soumettre(pk, request.user.id)
            return Response({
                'success': True,
                'message': 'Demande soumise avec succès',
                'demande': self._demande_to_dict(result)
            })
        except DomainException as e:
            return self.handle_exception(e)
    
    @action(detail=True, methods=['post'], url_path='assigner')
    def assigner(self, request: Request, pk: int):
        """
        Assigne un agent à une demande.
        
        ACCESS: Administrateur
        
        BODY:
            AssignDemandeSerializer
        """
        serializer = AssignDemandeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        dto = serializer.to_dto()
        
        try:
            result = self.demande_service.assigner_agent(
                pk, dto, request.user.id
            )
            return Response({
                'success': True,
                'message': 'Agent assigné avec succès',
                'demande': self._demande_to_dict(result)
            })
        except DomainException as e:
            return self.handle_exception(e)
    
    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request: Request, pk: int):
        """
        Change le statut d'une demande.
        
        BODY:
            StatusChangeSerializer
        """
        serializer = StatusChangeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        dto = serializer.to_dto()
        
        try:
            result = self.demande_service.changer_statut(
                pk, dto, request.user.id
            )
            return Response({
                'success': True,
                'message': f'Statut changé en {result.status}',
                'demande': self._demande_to_dict(result)
            })
        except DomainException as e:
            return self.handle_exception(e)
    
    @action(detail=False, methods=['get'], url_path='statistiques')
    def statistiques(self, request: Request):
        """
        Statistiques des demandes (admin seulement).
        
        ACCESS: Administrateur
        
        RESPONSE:
            Statistiques globales
        """
        if request.user.role != 'administrateur':
            return Response({
                'success': False,
                'error': {'message': 'Accès réservé aux administrateurs'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        stats = self.demande_service.get_statistics()
        
        return Response({
            'success': True,
            'statistiques': stats
        })
    
    def _demande_to_dict(self, demande) -> dict:
        """Convertit une demande en dictionnaire."""
        return {
            'id': demande.id,
            'numero_reference': demande.numero_reference,
            'citoyen_id': demande.citoyen_id,
            'citoyen_nom': demande.citoyen_nom,
            'service_id': demande.service_id,
            'service_nom': demande.service_nom,
            'agent_id': demande.agent_id,
            'agent_nom': demande.agent_nom,
            'titre': demande.titre,
            'description': demande.description,
            'type_document': demande.type_document,
            'status': demande.status,
            'status_display': demande.status_display,
            'is_overdue': demande.is_overdue,
            'created_at': demande.created_at.isoformat() if demande.created_at else None,
            'date_soumission': demande.date_soumission.isoformat() if demande.date_soumission else None,
            'priorite': demande.priorite
        }


# ============================================================================
# VIEWSET DOCUMENTS
# ============================================================================

class DocumentViewSet(ExceptionHandlerMixin, viewsets.ViewSet):
    """
    ViewSet pour la gestion des documents.
    
    ENDPOINTS:
        GET /documents/ - Liste (filtrée)
        POST /documents/ - Upload
        GET /documents/{id}/ - Détail
        DELETE /documents/{id}/ - Supprimer
        POST /documents/{id}/verifier/ - Vérifier (agent)
    
    PERMISSIONS:
        - Read: Owner de la demande, Agent assigné, Admin
        - Create: Owner de la demande, Agent assigné
        - Delete: Owner (document non vérifié), Admin
    """
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.document_service = None  # À injecter
    
    def list(self, request: Request):
        """Liste les documents accessibles."""
        demande_id = request.query_params.get('demande_id')
        
        if not demande_id:
            return Response({
                'success': False,
                'error': {'message': 'Paramètre demande_id requis'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = self.document_service.list_by_demande(
                int(demande_id), request.user.id
            )
            return Response({
                'success': True,
                'items': [self._doc_to_dict(d) for d in result]
            })
        except DomainException as e:
            return self.handle_exception(e)
    
    def create(self, request: Request):
        """Upload d'un nouveau document."""
        # Gérer le fichier uploadé
        fichier = request.FILES.get('fichier')
        
        if not fichier:
            return Response({
                'success': False,
                'error': {'message': 'Aucun fichier fourni'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UploadDocumentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        dto = serializer.to_dto(
            fichier_nom=fichier.name,
            fichier_taille=fichier.size,
            fichier_content_type=fichier.content_type
        )
        
        try:
            result = self.document_service.upload(
                request.user.id,
                fichier.read(),
                dto
            )
            return Response({
                'success': True,
                'message': 'Document uploadé avec succès',
                'document': self._doc_to_dict(result)
            }, status=status.HTTP_201_CREATED)
        except DomainException as e:
            return self.handle_exception(e)
    
    @action(detail=True, methods=['post'], url_path='verifier')
    def verifier(self, request: Request, pk: int):
        """Marque un document comme vérifié (agent)."""
        try:
            result = self.document_service.verifier(pk, request.user.id)
            return Response({
                'success': True,
                'message': 'Document vérifié',
                'document': self._doc_to_dict(result)
            })
        except DomainException as e:
            return self.handle_exception(e)
    
    def _doc_to_dict(self, doc) -> dict:
        """Convertit un document en dictionnaire."""
        return {
            'id': doc.id,
            'demande_id': doc.demande_id,
            'fichier_nom': doc.fichier_nom,
            'fichier_url': doc.fichier_url,
            'fichier_type': doc.fichier_type,
            'fichier_taille': doc.fichier_taille,
            'taille_readable': doc.taille_readable,
            'type_document': doc.type_document,
            'est_verifie': doc.est_verifie,
            'created_at': doc.created_at.isoformat() if doc.created_at else None
        }


# ============================================================================
# VIEWSET NOTIFICATIONS
# ============================================================================

class NotificationViewSet(ExceptionHandlerMixin, viewsets.ViewSet):
    """
    ViewSet pour les notifications.
    
    ENDPOINTS:
        GET /notifications/ - Liste
        GET /notifications/non-lues/ - Compter non lues
        POST /notifications/{id}/marquer-lu/ - Marquer comme lu
        POST /notifications/marquer-tout-lu/ - Marquer tout lu
    
    PERMISSIONS:
        - Read: Propriétaire uniquement
        - Write: Propriétaire uniquement
    """
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notification_service = None  # À injecter
    
    def list(self, request: Request):
        """
        Liste les notifications de l'utilisateur.
        
        QUERY PARAMS:
            - unread_only: true pour non lues uniquement
            - limit: nombre max (défaut 50)
        """
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        limit = int(request.query_params.get('limit', 50))
        
        result = self.notification_service.list_by_user(
            request.user.id,
            unread_only=unread_only,
            limit=limit
        )
        
        return Response({
            'success': True,
            'items': [self._notif_to_dict(n) for n in result]
        })
    
    @action(detail=False, methods=['get'], url_path='non-lues')
    def non_lues(self, request: Request):
        """Retourne le nombre de notifications non lues."""
        count = self.notification_service.count_unread(request.user.id)
        
        return Response({
            'success': True,
            'count': count
        })
    
    @action(detail=True, methods=['post'], url_path='marquer-lu')
    def marquer_lu(self, request: Request, pk: int):
        """Marque une notification comme lue."""
        try:
            result = self.notification_service.mark_as_read(
                pk, request.user.id
            )
            return Response({
                'success': True,
                'notification': self._notif_to_dict(result)
            })
        except DomainException as e:
            return self.handle_exception(e)
    
    @action(detail=False, methods=['post'], url_path='marquer-tout-lu')
    def marquer_tout_lu(self, request: Request):
        """Marque toutes les notifications comme lues."""
        count = self.notification_service.mark_all_as_read(request.user.id)
        
        return Response({
            'success': True,
            'message': f'{count} notification(s) marquée(s) comme lue(s)'
        })
    
    def _notif_to_dict(self, notif) -> dict:
        """Convertit une notification en dictionnaire."""
        return {
            'id': notif.id,
            'type_notification': notif.type_notification,
            'titre': notif.titre,
            'message': notif.message,
            'is_read': notif.is_read,
            'created_at': notif.created_at.isoformat() if notif.created_at else None,
            'demande_id': notif.demande_id,
            'lien_action': notif.lien_action
        }


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des services administratifs.
    
    PERMISSIONS:
        - List/Retrieve: Tous les utilisateurs authentifiés
        - Create/Update/Delete: Administrateurs uniquement
    
    ENDPOINTS:
        GET    /api/services/           → Liste des services actifs
        POST   /api/services/           → Créer un service (admin)
        GET    /api/services/{id}/      → Détail d'un service
        PUT    /api/services/{id}/      → Modifier (admin)
        DELETE /api/services/{id}/     → Supprimer (admin)
    
    NOTES:
        - Les services inactifs (est_actif=False) sont filtrés pour les citoyens
        - Les agents et admins voient tous les services
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtre les services selon le rôle de l'utilisateur.
        
        - Citoyens: uniquement services actifs
        - Agents/Admins: tous les services
        """
        user = self.request.user
        if user.is_citoyen:
            return Service.objects.filter(est_actif=True)
        return Service.objects.all()
    
    def get_permissions(self):
        """
        Permissions dynamiques selon l'action.
        
        - Lecture: tous authentifiés
        - Écriture: admin uniquement
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdministrateur()]
        return [IsAuthenticated()]
    
    def list(self, request: Request):
        """Liste paginée des services."""
        queryset = self.get_queryset()
        serializer = ServiceSerializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'items': serializer.data
        })
    
    def retrieve(self, request: Request, pk: int):
        """Détail d'un service."""
        try:
            service = self.get_queryset().get(pk=pk)
            serializer = ServiceSerializer(service)
            return Response({
                'success': True,
                'service': serializer.data
            })
        except Service.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Service non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request: Request):
        """Créer un nouveau service (admin uniquement)."""
        serializer = ServiceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = serializer.save()
        return Response({
            'success': True,
            'message': 'Service créé avec succès',
            'service': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request: Request, pk: int):
        """Modifier un service (admin uniquement)."""
        try:
            service = Service.objects.get(pk=pk)
            serializer = ServiceSerializer(service, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return Response({
                'success': True,
                'message': 'Service mis à jour',
                'service': serializer.data
            })
        except Service.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Service non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request: Request, pk: int):
        """Désactiver un service (soft delete, admin uniquement)."""
        try:
            service = Service.objects.get(pk=pk)
            service.est_actif = False
            service.save()
            return Response({
                'success': True,
                'message': 'Service désactivé'
            })
        except Service.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Service non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class RendezVousViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des rendez-vous.
    
    ARCHITECTURE:
        Ce ViewSet gère les rendez-vous via l'API REST.
        Pour les notifications temps réel (création, confirmation),
        utiliser le backend Node.js avec WebSocket.
    
    PERMISSIONS:
        - Citoyens: voir leurs propres RDV, confirmer/annuler
        - Agents: voir les RDV qui leurs sont assignés, créer des propositions
        - Admins: tout voir et tout modifier
    
    WORKFLOW:
        1. Agent crée une proposition (POST /api/rendez-vous/)
        2. Citoyen reçoit notification temps réel (via Node.js WebSocket)
        3. Citoyen confirme (POST /api/rendez-vous/{id}/confirmer/)
        4. Agent reçoit confirmation temps réel (via Node.js WebSocket)
    
    ENDPOINTS:
        GET    /api/rendez-vous/              → Liste
        POST   /api/rendez-vous/              → Créer proposition (agent)
        GET    /api/rendez-vous/{id}/         → Détail
        PUT    /api/rendez-vous/{id}/         → Modifier (agent/admin)
        DELETE /api/rendez-vous/{id}/         → Annuler
        POST   /api/rendez-vous/{id}/confirmer/ → Confirmer (citoyen)
        POST   /api/rendez-vous/{id}/annuler/   → Annuler
        POST   /api/rendez-vous/{id}/marquer-realise/ → Marquer comme réalisé
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtre les RDV selon le rôle de l'utilisateur.
        
        - Citoyens: RDV où ils sont citoyens
        - Agents: RDV où ils sont agents assignés
        - Admins: tous les RDV
        """
        user = self.request.user
        if user.is_admin:
            return RendezVous.objects.all()
        elif user.is_agent:
            return RendezVous.objects.filter(agent=user)
        else:
            return RendezVous.objects.filter(citoyen=user)
    
    def list(self, request: Request):
        """
        Liste paginée des rendez-vous.
        
        PARAMÈTRES QUERY:
            - status: filtrer par statut
            - date_from: date de début (YYYY-MM-DD)
            - date_to: date de fin (YYYY-MM-DD)
        """
        queryset = self.get_queryset()
        
        # Filtres optionnels
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        date_from = request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(date_rdv__gte=date_from)
        
        date_to = request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(date_rdv__lte=date_to)
        
        serializer = RDVSerializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'items': serializer.data
        })
    
    def retrieve(self, request: Request, pk: int):
        """Détail d'un rendez-vous."""
        try:
            rdv = self.get_queryset().get(pk=pk)
            serializer = RDVSerializer(rdv)
            return Response({
                'success': True,
                'rendez_vous': serializer.data
            })
        except RendezVous.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Rendez-vous non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request: Request):
        """
        Créer une proposition de rendez-vous.
        
        SEULEMENT pour les agents et admins.
        
        NOTIFICATION:
            Après création, une notification temps réel est envoyée
            via Node.js WebSocket au citoyen concerné.
        """
        if not (request.user.is_agent or request.user.is_admin):
            return Response({
                'success': False,
                'message': 'Seuls les agents peuvent créer des propositions de RDV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CreateRDVSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            dto = serializer.to_dto()
            rdv = RDVService.create_proposition(dto, request.user.id)
            
            # Notification temps réel via Node.js (WebSocket)
            # Cette partie est gérée par le backend Node
            # POST /api/notifications/notify sur Node.js
            
            return Response({
                'success': True,
                'message': 'Proposition de rendez-vous créée',
                'rendez_vous': self._rdv_to_dict(rdv)
            }, status=status.HTTP_201_CREATED)
            
        except DomainException as e:
            return self.handle_exception(e)
    
    @action(detail=True, methods=['post'], url_path='confirmer')
    def confirmer(self, request: Request, pk: int):
        """
        Confirmer un rendez-vous (citoyen).
        
        Le citoyen peut confirmer une proposition qui lui est faite.
        Après confirmation, notification temps réel à l'agent via Node.js.
        """
        try:
            rdv = self.get_queryset().get(pk=pk)
            
            # Vérifier que le citoyen est bien le destinataire
            if request.user.is_citoyen and rdv.citoyen_id != request.user.id:
                return Response({
                    'success': False,
                    'message': 'Vous ne pouvez pas confirmer ce rendez-vous'
                }, status=status.HTTP_403_FORBIDDEN)
            
            rdv.confirmer()
            
            # Notification temps réel à l'agent via Node.js
            # Gérée par le backend Node.js
            
            return Response({
                'success': True,
                'message': 'Rendez-vous confirmé'
            })
            
        except RendezVous.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Rendez-vous non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], url_path='annuler')
    def annuler(self, request: Request, pk: int):
        """
        Annuler un rendez-vous.
        
        Peut être fait par le citoyen (sa demande) ou l'agent (son RDV).
        """
        try:
            rdv = self.get_queryset().get(pk=pk)
            
            # Vérifier les permissions
            if request.user.is_citoyen and rdv.citoyen_id != request.user.id:
                return Response({
                    'success': False,
                    'message': 'Vous ne pouvez pas annuler ce rendez-vous'
                }, status=status.HTTP_403_FORBIDDEN)
            
            rdv.annuler()
            
            # Notification temps réel via Node.js
            
            return Response({
                'success': True,
                'message': 'Rendez-vous annulé'
            })
            
        except RendezVous.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Rendez-vous non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], url_path='marquer-realise')
    def marquer_realise(self, request: Request, pk: int):
        """Marquer un rendez-vous comme réalisé (agent uniquement)."""
        if not (request.user.is_agent or request.user.is_admin):
            return Response({
                'success': False,
                'message': 'Permission refusée'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            rdv = self.get_queryset().get(pk=pk)
            rdv.marquer_realise()
            return Response({
                'success': True,
                'message': 'Rendez-vous marqué comme réalisé'
            })
        except RendezVous.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Rendez-vous non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def _rdv_to_dict(self, rdv) -> dict:
        """Convertit un rendez-vous en dictionnaire."""
        return {
            'id': rdv.id,
            'demande_id': rdv.demande_id,
            'citoyen': {
                'id': rdv.citoyen.id,
                'nom': rdv.citoyen.nom_complet
            },
            'agent': {
                'id': rdv.agent.id,
                'nom': rdv.agent.nom_complet
            },
            'date_rdv': rdv.date_rdv.isoformat() if rdv.date_rdv else None,
            'heure_debut': rdv.heure_debut.isoformat() if rdv.heure_debut else None,
            'heure_fin': rdv.heure_fin.isoformat() if rdv.heure_fin else None,
            'lieu': rdv.lieu,
            'motif': rdv.motif,
            'status': rdv.status,
            'created_at': rdv.created_at.isoformat() if rdv.created_at else None
        }
