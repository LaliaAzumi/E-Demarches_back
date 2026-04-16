"""
================================================================================
MODULE: services.py
COUCHE: Application
RÔLE: Services métier (Use Cases) - Orchestration des opérations

ARCHITECTURE:
    Les services implémentent les cas d'utilisation (User Stories).
    Ils coordonnent les entités du Domain et les repositories de l'Infrastructure.

    AuthService: Inscription, connexion, gestion tokens
    DemandeService: CRUD demandes, workflow, assignation
    NotificationService: Envoi notifications, marquage lu
    RDVService: Gestion rendez-vous
    DocumentService: Upload, vérification documents

PRINCIPE: Un service = Un cas d'utilisation ou un groupe cohérent
AGILE: Services métiers = Implémentation des critères d'acceptance
================================================================================
"""

from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta
import secrets
import string

from ..domain.entities import (
    Utilisateur, CitoyenProfile, AgentProfile,
    Demande, Document, Notification, RendezVous
)
from ..domain.value_objects import Email, PhoneNumber, Role, Status
from ..domain.exceptions import (
    DomainException,
    ValidationException,
    NotFoundException,
    PermissionDeniedException,
    AuthenticationException,
    BusinessRuleException,
    ExceptionCode
)
from ..infrastructure.repositories import (
    BaseRepository,
    UtilisateurRepository,
    DemandeRepository,
    DocumentRepository,
    NotificationRepository
)
from ..infrastructure.external_services import (
    EmailServiceInterface,
    OAuthServiceInterface,
    FileStorageInterface,
    EmailMessage
)
from .dtos import (
    # Auth
    RegisterInputDTO, LoginInputDTO, OAuthInputDTO, AuthOutputDTO,
    # User
    UserDTO, UserUpdateInputDTO, ChangePasswordInputDTO,
    # Demande
    CreateDemandeInputDTO, UpdateDemandeInputDTO, DemandeDTO,
    AssignDemandeInputDTO, StatusChangeInputDTO,
    # Document
    UploadDocumentInputDTO, DocumentDTO,
    # RDV
    CreateRDVInputDTO, RDVDTO, ConfirmerRDVInputDTO,
    # Notification
    NotificationDTO, CreateNotificationInputDTO,
    # Service
    ServiceDTO,
    # Pagination
    PaginationInputDTO, PaginatedOutputDTO
)


# ============================================================================
# SERVICE AUTHENTIFICATION
# ============================================================================

class AuthService:
    """
    Service pour la gestion de l'authentification.
    
    RESPONSABILITÉS:
        - Inscription des utilisateurs
        - Connexion (email/password et OAuth)
        - Gestion des tokens JWT
        - Réinitialisation mot de passe
    
    USER STORIES COUVERTES:
        - En tant que citoyen, je veux m'inscrire
        - En tant qu'utilisateur, je veux me connecter
        - En tant qu'utilisateur, je veux réinitialiser mon mot de passe
    
    EXEMPLE:
        >>> auth_service = AuthService(user_repo, email_service)
        >>> result = auth_service.register(register_dto)
        >>> print(result.user.nom_complet)
    """
    
    def __init__(
        self,
        user_repository: UtilisateurRepository,
        email_service: EmailServiceInterface,
        oauth_service: Optional[OAuthServiceInterface] = None
    ):
        """
        Initialise le service avec ses dépendances.
        
        PARAMÈTRES:
            user_repository: Repository pour les utilisateurs
            email_service: Service d'envoi d'emails
            oauth_service: Service OAuth optionnel
        """
        self._user_repo = user_repository
        self._email_service = email_service
        self._oauth_service = oauth_service
    
    def register(self, dto: RegisterInputDTO) -> AuthOutputDTO:
        """
        Inscrit un nouvel utilisateur.
        
        PROCESSUS:
            1. Valide les données d'entrée
            2. Vérifie l'unicité de l'email
            3. Crée l'utilisateur et son profil citoyen
            4. Envoie l'email de confirmation
            5. Génère les tokens JWT
        
        PARAMÈTRES:
            dto: Données d'inscription
            
        RETOURNE:
            AuthOutputDTO avec tokens et infos utilisateur
            
        LÈVE:
            ValidationException: Si données invalides
            BusinessRuleException: Si email déjà utilisé
        """
        # Validation
        errors = dto.validate()
        if errors:
            return AuthOutputDTO(
                success=False,
                message="Validation échouée",
                errors=errors
            )
        
        # Vérifier unicité email
        email = Email(dto.email)
        if self._user_repo.email_exists(email):
            raise BusinessRuleException(
                message="Cet email est déjà utilisé",
                code=ExceptionCode.AUTH_EMAIL_EXISTS,
                details={'field': 'email'}
            )
        
        # Créer l'utilisateur
        user = Utilisateur(
            email=email,
            nom=dto.nom.strip().upper(),
            prenom=dto.prenom.strip().title(),
            telephone=PhoneNumber(dto.telephone) if dto.telephone else None,
            role=Role.CITOYEN,
            is_active=True
        )
        user.set_password(dto.password)  # À implémenter avec hash
        
        # Sauvegarder
        saved_user = self._user_repo.save(user)
        
        # Créer le profil citoyen
        profile = CitoyenProfile(utilisateur_id=saved_user.id)
        self._user_repo.save_citoyen_profile(profile)
        
        # Envoyer email de bienvenue
        self._send_welcome_email(saved_user)
        
        # Générer tokens (à implémenter avec JWT)
        access_token, refresh_token = self._generate_tokens(saved_user)
        
        return AuthOutputDTO(
            success=True,
            message="Inscription réussie",
            access_token=access_token,
            refresh_token=refresh_token,
            user=self._to_user_dto(saved_user),
            is_new_user=True
        )
    
    def login(self, dto: LoginInputDTO) -> AuthOutputDTO:
        """
        Authentifie un utilisateur avec email/password.
        
        PARAMÈTRES:
            dto: Credentials de connexion
            
        RETOURNE:
            AuthOutputDTO avec tokens si succès
            
        LÈVE:
            AuthenticationException: Si credentials invalides
        """
        errors = dto.validate()
        if errors:
            return AuthOutputDTO(
                success=False,
                message="Données invalides",
                errors=errors
            )
        
        email = Email(dto.email)
        user = self._user_repo.authenticate(email, dto.password)
        
        if not user:
            raise AuthenticationException(
                message="Email ou mot de passe incorrect",
                code=ExceptionCode.AUTH_INVALID_CREDENTIALS
            )
        
        if not user.is_active:
            raise AuthenticationException(
                message="Ce compte est désactivé",
                code=ExceptionCode.AUTH_ACCOUNT_DISABLED
            )
        
        # Mettre à jour dernière connexion
        self._user_repo.update_last_login(user.id)
        
        # Générer tokens
        access_token, refresh_token = self._generate_tokens(user)
        
        return AuthOutputDTO(
            success=True,
            message="Connexion réussie",
            access_token=access_token,
            refresh_token=refresh_token,
            user=self._to_user_dto(user)
        )
    
    def oauth_login(self, dto: OAuthInputDTO) -> AuthOutputDTO:
        """
        Authentifie via OAuth (Google, Facebook).
        
        PROCESSUS:
            1. Vérifie le token OAuth
            2. Cherche l'utilisateur par email ou social_id
            3. Crée l'utilisateur s'il n'existe pas
            4. Met à jour les infos OAuth
            5. Génère les tokens JWT
        
        PARAMÈTRES:
            dto: Token OAuth et provider
            
        RETOURNE:
            AuthOutputDTO avec tokens
        """
        if not self._oauth_service:
            return AuthOutputDTO(
                success=False,
                message="Service OAuth non configuré"
            )
        
        errors = dto.validate()
        if errors:
            return AuthOutputDTO(
                success=False,
                message="Données invalides",
                errors=errors
            )
        
        # Vérifier token OAuth
        oauth_info = self._oauth_service.verify_token(dto.access_token)
        if not oauth_info:
            raise AuthenticationException(
                message="Token OAuth invalide",
                auth_method=dto.provider
            )
        
        # Chercher utilisateur
        user = self._user_repo.find_by_social_id(dto.provider, oauth_info.social_id)
        is_new = False
        
        if not user:
            # Chercher par email
            user = self._user_repo.find_by_email(oauth_info.email)
            
            if user:
                # Lier le compte OAuth existant
                user.auth_provider = dto.provider
                user.social_id = oauth_info.social_id
                user.avatar_url = oauth_info.picture_url
                user = self._user_repo.save(user)
            else:
                # Créer nouvel utilisateur
                user = self._create_oauth_user(oauth_info, dto.provider)
                is_new = True
        
        # Générer tokens
        access_token, refresh_token = self._generate_tokens(user)
        
        return AuthOutputDTO(
            success=True,
            message="Connexion OAuth réussie",
            access_token=access_token,
            refresh_token=refresh_token,
            user=self._to_user_dto(user),
            is_new_user=is_new
        )
    
    def refresh_token(self, refresh_token: str) -> AuthOutputDTO:
        """
        Rafraîchit les tokens d'accès.
        
        PARAMÈTRES:
            refresh_token: Token de rafraîchissement
            
        RETOURNE:
            Nouveaux tokens
        """
        # Implémentation avec JWT
        # Vérifier validité, générer nouveau access_token
        pass
    
    def change_password(
        self,
        user_id: int,
        dto: ChangePasswordInputDTO
    ) -> AuthOutputDTO:
        """
        Change le mot de passe d'un utilisateur.
        
        PARAMÈTRES:
            user_id: ID de l'utilisateur
            dto: Ancien et nouveau mot de passe
            
        LÈVE:
            PermissionDeniedException: Si ancien mot de passe incorrect
        """
        errors = dto.validate()
        if errors:
            return AuthOutputDTO(
                success=False,
                message="Validation échouée",
                errors=errors
            )
        
        user = self._user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundException(
                message="Utilisateur non trouvé",
                resource_type='user',
                resource_id=user_id
            )
        
        # Vérifier ancien mot de passe
        if not user.check_password(dto.current_password):
            raise PermissionDeniedException(
                message="Mot de passe actuel incorrect"
            )
        
        # Mettre à jour
        user.set_password(dto.new_password)
        self._user_repo.save(user)
        
        # Notifier par email
        self._send_password_changed_email(user)
        
        return AuthOutputDTO(
            success=True,
            message="Mot de passe modifié avec succès"
        )
    
    # Méthodes privées -------------------------------------------------
    
    def _create_oauth_user(self, oauth_info, provider: str) -> Utilisateur:
        """Crée un utilisateur à partir des infos OAuth."""
        user = Utilisateur(
            email=oauth_info.email,
            nom=oauth_info.last_name or "Utilisateur",
            prenom=oauth_info.first_name or provider.title(),
            telephone=None,
            role=Role.CITOYEN,
            auth_provider=provider,
            social_id=oauth_info.social_id,
            avatar_url=oauth_info.picture_url
        )
        # Mot de passe aléatoire (inutilisé)
        user.set_password(secrets.token_urlsafe(32))
        user.set_unusable_password()
        
        saved = self._user_repo.save(user)
        
        # Créer profil citoyen
        profile = CitoyenProfile(utilisateur_id=saved.id)
        self._user_repo.save_citoyen_profile(profile)
        
        return saved
    
    def _generate_tokens(self, user: Utilisateur) -> Tuple[str, str]:
        """Génère les tokens JWT."""
        # Implémentation avec djangorestframework-simplejwt
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken()
        refresh['user_id'] = user.id
        refresh['email'] = str(user.email)
        refresh['role'] = user.role.value
        
        return str(refresh.access_token), str(refresh)
    
    def _to_user_dto(self, user: Utilisateur) -> UserDTO:
        """Convertit un Utilisateur en UserDTO."""
        return UserDTO(
            id=user.id,
            email=str(user.email),
            nom=user.nom,
            prenom=user.prenom,
            telephone=str(user.telephone) if user.telephone else "",
            role=user.role.value,
            role_display=user.role.label,
            is_active=user.is_active,
            created_at=user.created_at,
            avatar_url=user.avatar_url
        )
    
    def _send_welcome_email(self, user: Utilisateur) -> None:
        """Envoie l'email de bienvenue."""
        message = EmailMessage(
            to=[user.email],
            subject="Bienvenue sur notre plateforme",
            body=f"Bonjour {user.prenom},\n\nBienvenue !",
            html_body=f"<h1>Bonjour {user.prenom}</h1><p>Bienvenue !</p>"
        )
        self._email_service.send(message)
    
    def _send_password_changed_email(self, user: Utilisateur) -> None:
        """Notifie du changement de mot de passe."""
        message = EmailMessage(
            to=[user.email],
            subject="Votre mot de passe a été modifié",
            body="Votre mot de passe a été changé avec succès."
        )
        self._email_service.send(message)


# ============================================================================
# SERVICE DEMANDES
# ============================================================================

class DemandeService:
    """
    Service pour la gestion des demandes administratives.
    
    RESPONSABILITÉS:
        - CRUD demandes
        - Workflow de traitement
        - Assignation aux agents
        - Statistiques et reporting
    
    USER STORIES:
        - En tant que citoyen, je veux soumettre une demande
        - En tant qu'agent, je veux traiter une demande
        - En tant qu'admin, je veux voir les statistiques
    """
    
    def __init__(
        self,
        demande_repository: DemandeRepository,
        user_repository: UtilisateurRepository,
        notification_service: 'NotificationService'
    ):
        self._demande_repo = demande_repository
        self._user_repo = user_repository
        self._notification_service = notification_service
    
    def create(self, citoyen_id: int, dto: CreateDemandeInputDTO) -> DemandeDTO:
        """
        Crée une nouvelle demande (brouillon).
        
        PROCESSUS:
            1. Valide les données
            2. Crée la demande en statut 'brouillon'
            3. Génère la référence unique
        
        PARAMÈTRES:
            citoyen_id: ID du citoyen créateur
            dto: Données de la demande
            
        RETOURNE:
            DemandeDTO créée
        """
        errors = dto.validate()
        if errors:
            raise ValidationException(
                message="Validation échouée",
                details={'errors': errors}
            )
        
        demande = Demande(
            citoyen_id=citoyen_id,
            service_id=dto.service_id,
            titre=dto.titre,
            description=dto.description,
            type_document=dto.type_document,
            status='brouillon'
        )
        
        saved = self._demande_repo.save(demande)
        
        # Générer référence
        saved.numero_reference = self._demande_repo.generate_reference(saved)
        saved = self._demande_repo.save(saved)
        
        return self._to_dto(saved)
    
    def soumettre(self, demande_id: int, citoyen_id: int) -> DemandeDTO:
        """
        Soumet une demande pour traitement.
        
        TRANSITION: brouillon → soumise
        
        PARAMÈTRES:
            demande_id: ID de la demande
            citoyen_id: ID du citoyen (pour vérification)
            
        LÈVE:
            PermissionDeniedException: Si le citoyen n'est pas le propriétaire
            BusinessRuleException: Si statut invalide
        """
        demande = self._get_demande_and_check_owner(demande_id, citoyen_id)
        
        # Vérifier transition autorisée
        if demande.status != 'brouillon':
            raise BusinessRuleException(
                message="Seules les demandes en brouillon peuvent être soumises",
                code=ExceptionCode.DEMANDE_INVALID_STATUS,
                details={'current_status': demande.status}
            )
        
        # Effectuer transition
        demande.soumettre()
        saved = self._demande_repo.save(demande)
        
        # Notifier les agents du service
        self._notification_service.notifier_nouvelle_demande(saved)
        
        return self._to_dto(saved)
    
    def assigner_agent(
        self,
        demande_id: int,
        dto: AssignDemandeInputDTO,
        admin_id: int
    ) -> DemandeDTO:
        """
        Assigne une demande à un agent.
        
        PARAMÈTRES:
            demande_id: ID de la demande
            dto: ID de l'agent
            admin_id: ID de l'admin effectuant l'action
            
        LÈVE:
            PermissionDeniedException: Si l'utilisateur n'est pas admin
        """
        self._check_admin_permission(admin_id)
        
        errors = dto.validate()
        if errors:
            raise ValidationException(
                message="Données invalides",
                details={'errors': errors}
            )
        
        demande = self._demande_repo.find_by_id(demande_id)
        if not demande:
            raise NotFoundException(
                message="Demande non trouvée",
                resource_type='demande',
                resource_id=demande_id
            )
        
        # Vérifier agent existe et est bien un agent
        agent = self._user_repo.find_by_id(dto.agent_id)
        if not agent or not agent.is_agent:
            raise ValidationException(
                message="Agent invalide",
                field='agent_id'
            )
        
        demande.assigner_agent(dto.agent_id)
        saved = self._demande_repo.save(demande)
        
        # Notifier agent et citoyen
        self._notification_service.notifier_assignation(saved)
        
        return self._to_dto(saved)
    
    def changer_statut(
        self,
        demande_id: int,
        dto: StatusChangeInputDTO,
        user_id: int
    ) -> DemandeDTO:
        """
        Change le statut d'une demande.
        
        PARAMÈTRES:
            demande_id: ID de la demande
            dto: Nouveau statut et raison
            user_id: ID de l'utilisateur effectuant l'action
        """
        errors = dto.validate()
        if errors:
            raise ValidationException(
                message="Statut invalide",
                details={'errors': errors}
            )
        
        demande = self._demande_repo.find_by_id(demande_id)
        if not demande:
            raise NotFoundException(
                message="Demande non trouvée",
                resource_type='demande',
                resource_id=demande_id
            )
        
        # Vérifier permissions selon transition
        self._check_status_transition_permission(
            demande, dto.new_status, user_id
        )
        
        # Effectuer changement
        saved = self._demande_repo.change_status(
            demande_id,
            dto.new_status,
            user_id,
            dto.reason
        )
        
        # Notifier
        if dto.new_status in ['traitee', 'rejetee']:
            self._notification_service.notifier_cloture(saved)
        elif dto.new_status == 'en_attente':
            self._notification_service.notifier_attente(saved, dto.reason)
        
        return self._to_dto(saved)
    
    def get_by_id(self, demande_id: int, user_id: int) -> DemandeDTO:
        """
        Récupère une demande par ID avec vérification d'accès.
        
        PARAMÈTRES:
            demande_id: ID de la demande
            user_id: ID de l'utilisateur demandeur
            
        RETOURNE:
            DemandeDTO si autorisé
            
        LÈVE:
            NotFoundException: Si demande inexistante
            PermissionDeniedException: Si accès non autorisé
        """
        demande = self._demande_repo.find_by_id(demande_id)
        if not demande:
            raise NotFoundException(
                message="Demande non trouvée",
                resource_type='demande',
                resource_id=demande_id
            )
        
        user = self._user_repo.find_by_id(user_id)
        if not user.can_access(demande.citoyen_id):
            raise PermissionDeniedException(
                message="Vous n'avez pas accès à cette demande"
            )
        
        return self._to_dto(demande)
    
    def list_by_citoyen(
        self,
        citoyen_id: int,
        pagination: PaginationInputDTO,
        status: Optional[str] = None
    ) -> PaginatedOutputDTO:
        """
        Liste les demandes d'un citoyen.
        
        PARAMÈTRES:
            citoyen_id: ID du citoyen
            pagination: Paramètres de pagination
            status: Filtrer par statut optionnel
        """
        errors = pagination.validate()
        if errors:
            raise ValidationException(
                message="Paramètres de pagination invalides",
                details={'errors': errors}
            )
        
        demandes = self._demande_repo.find_by_citoyen(
            citoyen_id,
            limit=pagination.page_size,
            offset=pagination.offset
        )
        
        total = self._demande_repo.count({'citoyen_id': citoyen_id})
        
        items = [self._to_dto(d) for d in demandes]
        
        return self._to_paginated_dto(items, total, pagination)
    
    def list_by_agent(
        self,
        agent_id: int,
        pagination: PaginationInputDTO,
        status: Optional[str] = None
    ) -> PaginatedOutputDTO:
        """Liste les demandes assignées à un agent."""
        errors = pagination.validate()
        if errors:
            raise ValidationException(
                message="Paramètres de pagination invalides",
                details={'errors': errors}
            )
        
        demandes = self._demande_repo.find_by_agent(agent_id, status)
        items = [self._to_dto(d) for d in demandes]
        total = len(items)  # Simplifié
        
        return self._to_paginated_dto(items, total, pagination)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques globales des demandes."""
        by_status = self._demande_repo.get_statistics_by_status()
        
        return {
            'by_status': by_status,
            'total': sum(by_status.values()),
            'overdue': len(self._demande_repo.get_overdue_demandes())
        }
    
    # Méthodes privées -------------------------------------------------
    
    def _get_demande_and_check_owner(
        self,
        demande_id: int,
        citoyen_id: int
    ) -> Demande:
        """Récupère une demande et vérifie le propriétaire."""
        demande = self._demande_repo.find_by_id(demande_id)
        if not demande:
            raise NotFoundException(
                message="Demande non trouvée",
                resource_type='demande',
                resource_id=demande_id
            )
        
        if demande.citoyen_id != citoyen_id:
            raise PermissionDeniedException(
                message="Cette demande ne vous appartient pas"
            )
        
        return demande
    
    def _check_admin_permission(self, user_id: int) -> None:
        """Vérifie que l'utilisateur est admin."""
        user = self._user_repo.find_by_id(user_id)
        if not user or not user.is_admin:
            raise PermissionDeniedException(
                message="Accès réservé aux administrateurs",
                required_permission='admin'
            )
    
    def _check_status_transition_permission(
        self,
        demande: Demande,
        new_status: str,
        user_id: int
    ) -> None:
        """Vérifie les permissions pour une transition."""
        user = self._user_repo.find_by_id(user_id)
        
        # Certaines transitions réservées aux agents/admins
        agent_only_transitions = ['en_traitement', 'traitee', 'rejetee']
        
        if new_status in agent_only_transitions and not (user.is_agent or user.is_admin):
            raise PermissionDeniedException(
                message="Cette action est réservée aux agents"
            )
    
    def _to_dto(self, demande: Demande) -> DemandeDTO:
        """Convertit une Demande en DemandeDTO."""
        # Récupérer noms des relations
        citoyen = self._user_repo.find_by_id(demande.citoyen_id)
        agent = self._user_repo.find_by_id(demande.agent_id) if demande.agent_id else None
        
        return DemandeDTO(
            id=demande.id,
            numero_reference=demande.numero_reference,
            citoyen_id=demande.citoyen_id,
            citoyen_nom=citoyen.nom_complet if citoyen else "",
            service_id=demande.service_id,
            service_nom="",  # À récupérer via service repo
            agent_id=demande.agent_id,
            agent_nom=agent.nom_complet if agent else None,
            titre=demande.titre,
            description=demande.description,
            type_document=demande.type_document,
            status=demande.status,
            status_display=self._get_status_display(demande.status),
            created_at=demande.created_at,
            date_soumission=demande.date_soumission,
            date_debut_traitement=demande.date_debut_traitement,
            date_cloture=demande.date_cloture,
            date_echeance=demande.date_echeance,
            priorite=demande.priorite,
            is_overdue=demande.is_overdue,
            duree_traitement=demande.duree_traitement,
            status_history=demande.status_history
        )
    
    def _to_paginated_dto(
        self,
        items: List[Any],
        total: int,
        pagination: PaginationInputDTO
    ) -> PaginatedOutputDTO:
        """Crée un DTO paginé."""
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return PaginatedOutputDTO(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_previous=pagination.page > 1
        )
    
    def _get_status_display(self, status: str) -> str:
        """Retourne le label d'affichage d'un statut."""
        displays = {
            'brouillon': 'Brouillon',
            'soumise': 'Soumise',
            'en_traitement': 'En traitement',
            'en_attente': 'En attente',
            'traitee': 'Traitée',
            'rejetee': 'Rejetée',
            'archivee': 'Archivée'
        }
        return displays.get(status, status)


# ============================================================================
# SERVICE NOTIFICATIONS
# ============================================================================

class NotificationService:
    """
    Service pour la gestion des notifications.
    
    RESPONSABILITÉS:
        - Envoi de notifications
        - Marquage comme lu
        - Comptage des non lues
    """
    
    def __init__(
        self,
        notification_repository: NotificationRepository,
        user_repository: UtilisateurRepository,
        email_service: EmailServiceInterface
    ):
        self._notif_repo = notification_repository
        self._user_repo = user_repository
        self._email_service = email_service
    
    def create(self, dto: CreateNotificationInputDTO) -> NotificationDTO:
        """Crée une notification."""
        errors = dto.validate()
        if errors:
            raise ValidationException(
                message="Données invalides",
                details={'errors': errors}
            )
        
        notif = self._notif_repo.create_notification(
            destinataire_id=dto.destinataire_id,
            type_notif=dto.type_notification,
            titre=dto.titre,
            message=dto.message,
            demande_id=dto.demande_id,
            lien_action=dto.lien_action
        )
        
        # Envoyer email si notification importante
        if dto.type_notification in ['error', 'warning']:
            self._send_email_notification(notif)
        
        return self._to_dto(notif)
    
    def list_by_user(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[NotificationDTO]:
        """Liste les notifications d'un utilisateur."""
        notifs = self._notif_repo.find_by_destinataire(user_id, unread_only, limit)
        return [self._to_dto(n) for n in notifs]
    
    def count_unread(self, user_id: int) -> int:
        """Compte les notifications non lues."""
        return self._notif_repo.count_unread(user_id)
    
    def mark_as_read(self, notification_id: int, user_id: int) -> NotificationDTO:
        """Marque une notification comme lue."""
        notif = self._notif_repo.find_by_id(notification_id)
        if not notif:
            raise NotFoundException(
                message="Notification non trouvée",
                resource_type='notification',
                resource_id=notification_id
            )
        
        # Vérifier propriétaire
        if notif.destinataire_id != user_id:
            raise PermissionDeniedException(
                message="Cette notification ne vous appartient pas"
            )
        
        notif.marquer_lu()
        saved = self._notif_repo.save(notif)
        
        return self._to_dto(saved)
    
    def mark_all_as_read(self, user_id: int) -> int:
        """Marque toutes les notifications comme lues."""
        return self._notif_repo.mark_all_as_read(user_id)
    
    # Notifications métier ---------------------------------------------
    
    def notifier_nouvelle_demande(self, demande: Demande) -> None:
        """Notifie les agents d'une nouvelle demande."""
        # À implémenter: trouver les agents du service
        pass
    
    def notifier_assignation(self, demande: Demande) -> None:
        """Notifie l'agent et le citoyen de l'assignation."""
        # Notifier agent
        if demande.agent_id:
            self.create(CreateNotificationInputDTO(
                destinataire_id=demande.agent_id,
                type_notification='info',
                titre="Nouvelle demande assignée",
                message=f"La demande {demande.numero_reference} vous a été assignée",
                demande_id=demande.id
            ))
        
        # Notifier citoyen
        self.create(CreateNotificationInputDTO(
            destinataire_id=demande.citoyen_id,
            type_notification='info',
            titre="Votre demande est en traitement",
            message=f"Un agent a été assigné à votre demande {demande.numero_reference}",
            demande_id=demande.id
        ))
    
    def notifier_cloture(self, demande: Demande) -> None:
        """Notifie le citoyen de la clôture."""
        status_text = "traitée" if demande.status == 'traitee' else "rejetée"
        
        self.create(CreateNotificationInputDTO(
            destinataire_id=demande.citoyen_id,
            type_notification='success' if demande.status == 'traitee' else 'warning',
            titre=f"Votre demande a été {status_text}",
            message=f"La demande {demande.numero_reference} est {status_text}",
            demande_id=demande.id
        ))
    
    def notifier_attente(self, demande: Demande, motif: str) -> None:
        """Notifie le citoyen d'une mise en attente."""
        self.create(CreateNotificationInputDTO(
            destinataire_id=demande.citoyen_id,
            type_notification='warning',
            titre="Documents complémentaires requis",
            message=f"Votre demande {demande.numero_reference} est en attente: {motif}",
            demande_id=demande.id
        ))
    
    # Méthodes privées -------------------------------------------------
    
    def _to_dto(self, notif: Notification) -> NotificationDTO:
        """Convertit en DTO."""
        return NotificationDTO(
            id=notif.id,
            type_notification=notif.type_notification,
            titre=notif.titre,
            message=notif.message,
            is_read=notif.is_read,
            created_at=notif.created_at,
            date_lecture=notif.date_lecture,
            demande_id=notif.demande_id,
            lien_action=notif.lien_action
        )
    
    def _send_email_notification(self, notif: Notification) -> None:
        """Envoie un email pour une notification importante."""
        user = self._user_repo.find_by_id(notif.destinataire_id)
        if user:
            message = EmailMessage(
                to=[user.email],
                subject=notif.titre,
                body=notif.message
            )
            self._email_service.send(message)


# ============================================================================
# SERVICE RDV
# ============================================================================

class RDVService:
    """
    Service pour la gestion des rendez-vous.
    
    RESPONSABILITÉS:
        - Création de propositions
        - Confirmation par citoyen
        - Annulation
        - Gestion des conflits
    """
    
    def __init__(
        self,
        demande_repository: DemandeRepository,
        user_repository: UtilisateurRepository
    ):
        self._demande_repo = demande_repository
        self._user_repo = user_repository
    
    def proposer(self, agent_id: int, dto: CreateRDVInputDTO) -> RDVDTO:
        """
        Propose un rendez-vous à un citoyen.
        
        Seul l'agent assigné à la demande peut proposer un RDV.
        """
        errors = dto.validate()
        if errors:
            raise ValidationException(
                message="Données invalides",
                details={'errors': errors}
            )
        
        demande = self._demande_repo.find_by_id(dto.demande_id)
        if not demande:
            raise NotFoundException(
                message="Demande non trouvée",
                resource_type='demande',
                resource_id=dto.demande_id
            )
        
        # Vérifier que l'agent est assigné
        if demande.agent_id != agent_id:
            raise PermissionDeniedException(
                message="Vous n'êtes pas assigné à cette demande"
            )
        
        # Vérifier pas de conflit
        # À implémenter: vérifier disponibilité
        
        rdv = RendezVous(
            demande_id=dto.demande_id,
            citoyen_id=demande.citoyen_id,
            agent_id=agent_id,
            date_rdv=datetime.strptime(dto.date_rdv, '%Y-%m-%d').date(),
            heure_debut=dto.heure_debut,
            heure_fin=dto.heure_fin,
            lieu=dto.lieu,
            motif=dto.motif
        )
        
        # Sauvegarder via repository
        # saved = self._rdv_repo.save(rdv)
        
        return self._to_dto(rdv)
    
    def confirmer(self, citoyen_id: int, dto: ConfirmerRDVInputDTO) -> RDVDTO:
        """Confirme un rendez-vous proposé."""
        errors = dto.validate()
        if errors:
            raise ValidationException(
                message="Données invalides",
                details={'errors': errors}
            )
        
        # Récupérer et vérifier RDV
        # rdv = self._rdv_repo.find_by_id(dto.rdv_id)
        # if not rdv or rdv.citoyen_id != citoyen_id:
        #     raise PermissionDeniedException()
        
        # rdv.confirmer()
        # saved = self._rdv_repo.save(rdv)
        
        # return self._to_dto(saved)
        pass
    
    def _to_dto(self, rdv: RendezVous) -> RDVDTO:
        """Convertit en DTO."""
        return RDVDTO(
            id=rdv.id,
            demande_id=rdv.demande_id,
            citoyen_id=rdv.citoyen_id,
            citoyen_nom="",  # À récupérer
            agent_id=rdv.agent_id,
            agent_nom="",  # À récupérer
            date_rdv=rdv.date_rdv,
            heure_debut=rdv.heure_debut,
            heure_fin=rdv.heure_fin,
            lieu=rdv.lieu,
            motif=rdv.motif,
            status=rdv.status,
            status_display=rdv.status,
            created_at=rdv.created_at
        )


# ============================================================================
# SERVICE DOCUMENTS
# ============================================================================

class DocumentService:
    """
    Service pour la gestion des documents.
    
    RESPONSABILITÉS:
        - Upload de fichiers
        - Vérification par agents
        - Stockage sécurisé
    """
    
    def __init__(
        self,
        document_repository: DocumentRepository,
        demande_repository: DemandeRepository,
        file_storage: FileStorageInterface
    ):
        self._doc_repo = document_repository
        self._demande_repo = demande_repository
        self._file_storage = file_storage
    
    def upload(
        self,
        user_id: int,
        file_content: bytes,
        dto: UploadDocumentInputDTO
    ) -> DocumentDTO:
        """
        Upload un document pour une demande.
        
        PARAMÈTRES:
            user_id: ID de l'utilisateur uploadant
            file_content: Contenu binaire du fichier
            dto: Métadonnées du document
        """
        errors = dto.validate()
        if errors:
            raise ValidationException(
                message="Fichier invalide",
                details={'errors': errors}
            )
        
        # Vérifier accès à la demande
        demande = self._demande_repo.find_by_id(dto.demande_id)
        if not demande:
            raise NotFoundException(
                message="Demande non trouvée",
                resource_type='demande',
                resource_id=dto.demande_id
            )
        
        # Vérifier propriétaire ou agent
        if demande.citoyen_id != user_id and demande.agent_id != user_id:
            raise PermissionDeniedException(
                message="Vous ne pouvez pas ajouter de document à cette demande"
            )
        
        # Sauvegarder fichier
        storage_path = f"documents/{dto.demande_id}/{dto.fichier_nom}"
        self._file_storage.save(storage_path, file_content, dto.fichier_content_type)
        
        # Créer document
        doc = Document(
            demande_id=dto.demande_id,
            uploaded_by_id=user_id,
            fichier_nom=dto.fichier_nom,
            fichier_chemin=storage_path,
            fichier_type=dto.fichier_content_type,
            fichier_taille=dto.fichier_taille,
            type_document=dto.type_document,
            description=dto.description
        )
        
        saved = self._doc_repo.save(doc)
        
        return self._to_dto(saved)
    
    def verifier(self, document_id: int, agent_id: int) -> DocumentDTO:
        """Marque un document comme vérifié par un agent."""
        doc = self._doc_repo.mark_as_verified(document_id, agent_id)
        return self._to_dto(doc)
    
    def list_by_demande(self, demande_id: int, user_id: int) -> List[DocumentDTO]:
        """Liste les documents d'une demande."""
        # Vérifier accès
        demande = self._demande_repo.find_by_id(demande_id)
        if not demande:
            raise NotFoundException(
                message="Demande non trouvée",
                resource_type='demande',
                resource_id=demande_id
            )
        
        user = self._user_repo.find_by_id(user_id)
        if not user.can_access(demande.citoyen_id):
            raise PermissionDeniedException()
        
        docs = self._doc_repo.find_by_demande(demande_id)
        return [self._to_dto(d) for d in docs]
    
    def _to_dto(self, doc: Document) -> DocumentDTO:
        """Convertit en DTO."""
        return DocumentDTO(
            id=doc.id,
            demande_id=doc.demande_id,
            fichier_nom=doc.fichier_nom,
            fichier_url=self._file_storage.get_url(doc.fichier_chemin),
            fichier_type=doc.fichier_type,
            fichier_taille=doc.fichier_taille,
            taille_readable=doc.taille_readable,
            type_document=doc.type_document,
            type_display=doc.type_document,
            description=doc.description,
            est_verifie=doc.est_verifie,
            created_at=doc.created_at,
            uploaded_by_nom=""  # À récupérer
        )
