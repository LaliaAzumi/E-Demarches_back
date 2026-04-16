"""
================================================================================
MODULE: serializers.py
COUCHE: Presentation
RÔLE: Sérializers DRF - Adaptation DTOs ↔ JSON

ARCHITECTURE:
    Les sérializers convertissent entre:
    - DTOs Python (Application Layer) et JSON (HTTP)
    - Ils valident les données entrantes
    - Ils formatent les données sortantes

    INPUT: JSON → Validation → DTO → Service
    OUTPUT: Entity → DTO → JSON

PATTERN: Serializer Pattern (Django REST Framework)
AGILE: Serializers = Data Contracts pour l'API
================================================================================
"""

from rest_framework import serializers
from typing import Dict, Any, List

from ..domain.value_objects import Email, PhoneNumber, Role
from ..domain.exceptions import ValidationException
from ..application.dtos import (
    # Input DTOs
    RegisterInputDTO, LoginInputDTO, OAuthInputDTO,
    CreateDemandeInputDTO, UpdateDemandeInputDTO,
    AssignDemandeInputDTO, StatusChangeInputDTO,
    UploadDocumentInputDTO,
    CreateRDVInputDTO,
    CreateNotificationInputDTO,
    PaginationInputDTO,
    # Output DTOs
    UserDTO, DemandeDTO, DocumentDTO, NotificationDTO, RDVDTO,
    AuthOutputDTO, PaginatedOutputDTO
)


# ============================================================================
# SÉRIALIZERS D'AUTENTIFICATION
# ============================================================================

class RegisterSerializer(serializers.Serializer):
    """
    Sérializer pour l'inscription.
    
    FIELDS:
        - email (required): Email unique
        - password (required, min 8): Mot de passe
        - password_confirm (required): Confirmation
        - nom (required): Nom de famille
        - prenom (required): Prénom
        - telephone (optional): Numéro de téléphone
    
    VALIDATION:
        - Mots de passe identiques
        - Email valide
        - Téléphone sénégalais
    
    EXEMPLE:
        >>> data = {
        ...     'email': 'test@example.com',
        ...     'password': 'SecurePass123',
        ...     'password_confirm': 'SecurePass123',
        ...     'nom': 'DIOP',
        ...     'prenom': 'Amadou'
        ... }
        >>> serializer = RegisterSerializer(data=data)
        >>> if serializer.is_valid():
        ...     dto = serializer.to_dto()
    """
    
    # Champs requis
    email = serializers.EmailField(
        required=True,
        help_text="Email unique de l'utilisateur",
        error_messages={
            'required': "L'email est obligatoire",
            'invalid': "Format d'email invalide"
        }
    )
    
    password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        help_text="Mot de passe (min. 8 caractères)",
        error_messages={
            'min_length': "Le mot de passe doit contenir au moins 8 caractères",
            'required': "Le mot de passe est obligatoire"
        }
    )
    
    password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Confirmation du mot de passe"
    )
    
    nom = serializers.CharField(
        required=True,
        min_length=2,
        max_length=100,
        help_text="Nom de famille",
        error_messages={
            'min_length': "Le nom doit contenir au moins 2 caractères",
            'required': "Le nom est obligatoire"
        }
    )
    
    prenom = serializers.CharField(
        required=True,
        min_length=2,
        max_length=100,
        help_text="Prénom",
        error_messages={
            'min_length': "Le prénom doit contenir au moins 2 caractères",
            'required': "Le prénom est obligatoire"
        }
    )
    
    # Champs optionnels
    telephone = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
        help_text="Numéro de téléphone (format: 77 XXX XX XX)"
    )
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validation globale du serializer.
        
        VÉRIFIE:
            - Correspondance des mots de passe
        """
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': "Les mots de passe ne correspondent pas"
            })
        
        return data
    
    def validate_telephone(self, value: str) -> str:
        """
        Validation du numéro de téléphone.
        
        FORMAT ACCEPTÉ:
            - 77 XXX XX XX
            - +221 77 XXX XX XX
            - 77XXXXXXX
        """
        if not value:
            return value
        
        # Nettoyer et valider avec le Value Object
        try:
            phone = PhoneNumber(value)
            return str(phone)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
    
    def to_dto(self) -> RegisterInputDTO:
        """
        Convertit les données validées en DTO.
        
        RETOURNE:
            RegisterInputDTO pour le service
        """
        return RegisterInputDTO(
            email=self.validated_data['email'],
            password=self.validated_data['password'],
            password_confirm=self.validated_data['password_confirm'],
            nom=self.validated_data['nom'],
            prenom=self.validated_data['prenom'],
            telephone=self.validated_data.get('telephone', '')
        )


class LoginSerializer(serializers.Serializer):
    """
    Sérializer pour la connexion.
    
    FIELDS:
        - email (required): Email
        - password (required): Mot de passe
    """
    
    email = serializers.EmailField(
        required=True,
        help_text="Email de connexion"
    )
    
    password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Mot de passe"
    )
    
    def to_dto(self) -> LoginInputDTO:
        """Convertit en DTO."""
        return LoginInputDTO(
            email=self.validated_data['email'],
            password=self.validated_data['password']
        )


class OAuthSerializer(serializers.Serializer):
    """
    Sérializer pour l'authentification OAuth.
    
    FIELDS:
        - provider (required): 'google' ou 'facebook'
        - access_token (required): Token OAuth
    """
    
    PROVIDER_CHOICES = [
        ('google', 'Google'),
        ('facebook', 'Facebook')
    ]
    
    provider = serializers.ChoiceField(
        choices=PROVIDER_CHOICES,
        required=True,
        help_text="Provider OAuth"
    )
    
    access_token = serializers.CharField(
        required=True,
        min_length=20,
        help_text="Token d'accès OAuth",
        error_messages={
            'min_length': "Token d'accès invalide (trop court)"
        }
    )
    
    def to_dto(self) -> OAuthInputDTO:
        """Convertit en DTO."""
        return OAuthInputDTO(
            provider=self.validated_data['provider'],
            access_token=self.validated_data['access_token']
        )


class RefreshTokenSerializer(serializers.Serializer):
    """
    Sérializer pour le rafraîchissement de token.
    
    FIELDS:
        - refresh_token (required): Token de rafraîchissement
    """
    
    refresh_token = serializers.CharField(
        required=True,
        help_text="Token de rafraîchissement JWT"
    )


# ============================================================================
# SÉRIALIZERS UTILISATEUR
# ============================================================================

class UtilisateurSerializer(serializers.Serializer):
    """
    Sérializer pour la représentation des utilisateurs.
    
    UTILISATION:
        - Réponse API (lecture)
        - Mise à jour profil (écriture partielle)
    
    FIELDS (lecture):
        - id, email, nom, prenom
        - telephone, role, role_display
        - is_active, nom_complet
        - created_at, avatar_url
    """
    
    # Identité (read-only)
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    
    # Profil
    nom = serializers.CharField(max_length=100)
    prenom = serializers.CharField(max_length=100)
    telephone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Rôle (read-only pour les citoyens)
    role = serializers.CharField(read_only=True)
    role_display = serializers.CharField(read_only=True, source='role_display')
    
    # Calculés
    nom_complet = serializers.CharField(read_only=True, source='nom_complet')
    
    # Statut
    is_active = serializers.BooleanField(read_only=True)
    
    # Métadonnées
    created_at = serializers.DateTimeField(read_only=True)
    avatar_url = serializers.URLField(read_only=True, required=False)
    
    def get_role_display(self, obj: UserDTO) -> str:
        """Retourne le label du rôle."""
        try:
            role = Role(obj.role)
            return role.label
        except ValueError:
            return obj.role
    
    def validate_telephone(self, value: str) -> str:
        """Valide le téléphone."""
        if not value:
            return value
        try:
            phone = PhoneNumber(value)
            return str(phone)
        except ValueError as e:
            raise serializers.ValidationError(str(e))


class ChangePasswordSerializer(serializers.Serializer):
    """
    Sérializer pour changer le mot de passe.
    
    FIELDS:
        - current_password (required): Mot de passe actuel
        - new_password (required, min 8): Nouveau mot de passe
        - new_password_confirm (required): Confirmation
    """
    
    current_password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Mot de passe actuel"
    )
    
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        help_text="Nouveau mot de passe (min. 8 caractères)"
    )
    
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Confirmation du nouveau mot de passe"
    )
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie que les nouveaux mots de passe correspondent."""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': "Les mots de passe ne correspondent pas"
            })
        return data


# ============================================================================
# SÉRIALIZERS DEMANDES
# ============================================================================

class CreateDemandeSerializer(serializers.Serializer):
    """
    Sérializer pour créer une demande.
    
    FIELDS:
        - service_id (required): ID du service
        - titre (required, min 5): Titre de la demande
        - description (required, min 10): Description détaillée
        - type_document (required): Type de document demandé
    """
    
    service_id = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="ID du service administratif"
    )
    
    titre = serializers.CharField(
        required=True,
        min_length=5,
        max_length=200,
        help_text="Titre de la demande (min. 5 caractères)"
    )
    
    description = serializers.CharField(
        required=True,
        min_length=10,
        help_text="Description détaillée (min. 10 caractères)"
    )
    
    type_document = serializers.CharField(
        required=True,
        max_length=50,
        help_text="Type de document (acte_naissance, acte_mariage, etc.)"
    )
    
    def to_dto(self) -> CreateDemandeInputDTO:
        """Convertit en DTO."""
        return CreateDemandeInputDTO(
            service_id=self.validated_data['service_id'],
            titre=self.validated_data['titre'],
            description=self.validated_data['description'],
            type_document=self.validated_data['type_document']
        )


class UpdateDemandeSerializer(serializers.Serializer):
    """
    Sérializer pour modifier une demande (brouillon uniquement).
    
    FIELDS (tous optionnels):
        - titre: Nouveau titre
        - description: Nouvelle description
    """
    
    titre = serializers.CharField(
        required=False,
        min_length=5,
        max_length=200,
        help_text="Nouveau titre"
    )
    
    description = serializers.CharField(
        required=False,
        min_length=10,
        help_text="Nouvelle description"
    )
    
    def to_dto(self) -> UpdateDemandeInputDTO:
        """Convertit en DTO."""
        return UpdateDemandeInputDTO(
            titre=self.validated_data.get('titre'),
            description=self.validated_data.get('description')
        )


class StatusChangeSerializer(serializers.Serializer):
    """
    Sérializer pour changer le statut d'une demande.
    
    FIELDS:
        - new_status (required): Nouveau statut
        - reason (optional): Raison du changement
    """
    
    STATUS_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumise', 'Soumise'),
        ('en_traitement', 'En traitement'),
        ('en_attente', 'En attente'),
        ('traitee', 'Traitée'),
        ('rejetee', 'Rejetée'),
        ('archivee', 'Archivée'),
    ]
    
    new_status = serializers.ChoiceField(
        choices=STATUS_CHOICES,
        required=True,
        help_text="Nouveau statut"
    )
    
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Raison du changement (requis pour certains statuts)"
    )
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validation: motif requis pour rejetee et en_attente.
        """
        if data['new_status'] in ['rejetee', 'en_attente']:
            if not data.get('reason'):
                raise serializers.ValidationError({
                    'reason': "Un motif est requis pour ce changement de statut"
                })
        return data
    
    def to_dto(self) -> StatusChangeInputDTO:
        """Convertit en DTO."""
        return StatusChangeInputDTO(
            new_status=self.validated_data['new_status'],
            reason=self.validated_data.get('reason')
        )


class AssignDemandeSerializer(serializers.Serializer):
    """
    Sérializer pour assigner un agent à une demande.
    
    FIELDS:
        - agent_id (required): ID de l'agent
    """
    
    agent_id = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="ID de l'agent à assigner"
    )
    
    def to_dto(self) -> AssignDemandeInputDTO:
        """Convertit en DTO."""
        return AssignDemandeInputDTO(
            agent_id=self.validated_data['agent_id']
        )


class DemandeSerializer(serializers.Serializer):
    """
    Sérializer pour représenter une demande (lecture).
    
    FIELDS:
        - Identité: id, numero_reference
        - Relations: citoyen_id, citoyen_nom, service_id, service_nom, agent_id, agent_nom
        - Contenu: titre, description, type_document
        - Statut: status, status_display, is_overdue
        - Dates: created_at, date_soumission, date_cloture, duree_traitement
    """
    
    # Identité
    id = serializers.IntegerField()
    numero_reference = serializers.CharField()
    
    # Relations
    citoyen_id = serializers.IntegerField()
    citoyen_nom = serializers.CharField()
    service_id = serializers.IntegerField()
    service_nom = serializers.CharField()
    agent_id = serializers.IntegerField(required=False, allow_null=True)
    agent_nom = serializers.CharField(required=False, allow_null=True)
    
    # Contenu
    titre = serializers.CharField()
    description = serializers.CharField()
    type_document = serializers.CharField()
    
    # Statut
    status = serializers.CharField()
    status_display = serializers.CharField()
    is_overdue = serializers.BooleanField()
    priorite = serializers.CharField()
    
    # Dates
    created_at = serializers.DateTimeField()
    date_soumission = serializers.DateTimeField(required=False, allow_null=True)
    date_debut_traitement = serializers.DateTimeField(required=False, allow_null=True)
    date_cloture = serializers.DateTimeField(required=False, allow_null=True)
    date_echeance = serializers.DateTimeField(required=False, allow_null=True)
    duree_traitement = serializers.IntegerField(required=False, allow_null=True)
    
    # Historique
    status_history = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )


class DemandeListSerializer(serializers.Serializer):
    """
    Sérializer simplifié pour les listes de demandes.
    
    Moins de champs pour optimiser les performances.
    """
    
    id = serializers.IntegerField()
    numero_reference = serializers.CharField()
    titre = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    created_at = serializers.DateTimeField()
    is_overdue = serializers.BooleanField()


# ============================================================================
# SÉRIALIZERS DOCUMENTS
# ============================================================================

class UploadDocumentSerializer(serializers.Serializer):
    """
    Sérializer pour uploader un document.
    
    FIELDS:
        - demande_id (required): ID de la demande
        - type_document (required): Type de document
        - description (optional): Description
        - fichier: Fichier (géré par ViewSet)
    """
    
    TYPE_CHOICES = [
        ('piece_identite', 'Pièce d\'identité'),
        ('justificatif', 'Justificatif'),
        ('formulaire', 'Formulaire'),
        ('attestation', 'Attestation'),
        ('autre', 'Autre'),
    ]
    
    demande_id = serializers.IntegerField(
        required=True,
        help_text="ID de la demande concernée"
    )
    
    type_document = serializers.ChoiceField(
        choices=TYPE_CHOICES,
        required=True,
        help_text="Type de document"
    )
    
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Description du document"
    )
    
    def to_dto(self, fichier_nom: str, fichier_taille: int, 
               fichier_content_type: str) -> UploadDocumentInputDTO:
        """Convertit en DTO avec infos fichier."""
        return UploadDocumentInputDTO(
            demande_id=self.validated_data['demande_id'],
            type_document=self.validated_data['type_document'],
            description=self.validated_data.get('description'),
            fichier_nom=fichier_nom,
            fichier_taille=fichier_taille,
            fichier_content_type=fichier_content_type
        )


class DocumentSerializer(serializers.Serializer):
    """
    Sérializer pour représenter un document.
    """
    
    id = serializers.IntegerField()
    demande_id = serializers.IntegerField()
    
    fichier_nom = serializers.CharField()
    fichier_url = serializers.URLField()
    fichier_type = serializers.CharField()
    fichier_taille = serializers.IntegerField()
    taille_readable = serializers.CharField()
    
    type_document = serializers.CharField()
    type_display = serializers.CharField()
    description = serializers.CharField(required=False, allow_null=True)
    est_verifie = serializers.BooleanField()
    
    created_at = serializers.DateTimeField()
    uploaded_by_nom = serializers.CharField()


# ============================================================================
# SÉRIALIZERS NOTIFICATIONS
# ============================================================================

class NotificationSerializer(serializers.Serializer):
    """
    Sérializer pour les notifications.
    """
    
    id = serializers.IntegerField()
    type_notification = serializers.CharField()
    titre = serializers.CharField()
    message = serializers.CharField()
    
    is_read = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    date_lecture = serializers.DateTimeField(required=False, allow_null=True)
    
    demande_id = serializers.IntegerField(required=False, allow_null=True)
    lien_action = serializers.URLField(required=False, allow_null=True)


# ============================================================================
# SÉRIALIZERS RDV
# ============================================================================

class CreateRDVSerializer(serializers.Serializer):
    """
    Sérializer pour créer un rendez-vous.
    
    FIELDS:
        - demande_id (required): ID de la demande
        - date_rdv (required): Date (YYYY-MM-DD)
        - heure_debut (required): Heure début (HH:MM)
        - heure_fin (required): Heure fin (HH:MM)
        - lieu (required): Lieu du RDV
        - motif (optional): Motif
    """
    
    demande_id = serializers.IntegerField(required=True)
    date_rdv = serializers.DateField(required=True, format='%Y-%m-%d')
    heure_debut = serializers.TimeField(required=True, format='%H:%M')
    heure_fin = serializers.TimeField(required=True, format='%H:%M')
    lieu = serializers.CharField(required=True, max_length=200)
    motif = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie que l'heure de fin est après l'heure de début."""
        if data['heure_fin'] <= data['heure_debut']:
            raise serializers.ValidationError({
                'heure_fin': "L'heure de fin doit être après l'heure de début"
            })
        return data


class RDVSerializer(serializers.Serializer):
    """
    Sérializer pour représenter un rendez-vous.
    """
    
    id = serializers.IntegerField()
    demande_id = serializers.IntegerField()
    
    citoyen_id = serializers.IntegerField()
    citoyen_nom = serializers.CharField()
    agent_id = serializers.IntegerField()
    agent_nom = serializers.CharField()
    
    date_rdv = serializers.DateField()
    heure_debut = serializers.TimeField()
    heure_fin = serializers.TimeField()
    
    lieu = serializers.CharField()
    motif = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    
    created_at = serializers.DateTimeField()
    date_confirmation = serializers.DateTimeField(required=False, allow_null=True)


# ============================================================================
# SÉRIALIZERS UTILITAIRES
# ============================================================================

class PaginationSerializer(serializers.Serializer):
    """
    Sérializer pour les paramètres de pagination.
    
    QUERY PARAMS:
        - page (default 1): Numéro de page
        - page_size (default 20): Taille de page (max 100)
    """
    
    page = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="Numéro de page (défaut: 1)"
    )
    
    page_size = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100,
        help_text="Nombre d'éléments par page (max: 100)"
    )
    
    def to_dto(self) -> PaginationInputDTO:
        """Convertit en DTO."""
        return PaginationInputDTO(
            page=self.validated_data.get('page', 1),
            page_size=self.validated_data.get('page_size', 20)
        )


class PaginatedResponseSerializer(serializers.Serializer):
    """
    Sérializer pour les réponses paginées.
    
    STRUCTURE:
        {
            'success': true,
            'items': [...],
            'total': 100,
            'page': 1,
            'page_size': 20,
            'total_pages': 5,
            'has_next': true,
            'has_previous': false,
            'next_page': 2,
            'previous_page': null
        }
    """
    
    success = serializers.BooleanField(default=True)
    items = serializers.ListField(child=serializers.DictField())
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()
    next_page = serializers.IntegerField(required=False, allow_null=True)
    previous_page = serializers.IntegerField(required=False, allow_null=True)


class ErrorResponseSerializer(serializers.Serializer):
    """
    Sérializer standardisé pour les erreurs.
    
    STRUCTURE:
        {
            'success': false,
            'error': {
                'code': 'ERR_1001',
                'message': 'Message explicatif',
                'field': 'email',
                'details': {...}
            }
        }
    """
    
    success = serializers.BooleanField(default=False)
    
    error = serializers.DictField(
        child=serializers.CharField(),
        help_text="Détails de l'erreur"
    )
    
    message = serializers.CharField(
        required=False,
        help_text="Message global (optionnel)"
    )


class SuccessResponseSerializer(serializers.Serializer):
    """
    Sérializer standardisé pour les succès.
    
    STRUCTURE:
        {
            'success': true,
            'message': 'Opération réussie',
            'data': {...}
        }
    """
    
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = serializers.DictField(required=False)


# ============================================================================
# SÉRIALIZERS API RÉPONSE
# ============================================================================

class AuthResponseSerializer(serializers.Serializer):
    """
    Sérializer pour les réponses d'authentification.
    
    STRUCTURE:
        {
            'success': true,
            'message': 'Connexion réussie',
            'access_token': '...',
            'refresh_token': '...',
            'user': {...},
            'is_new_user': false
        }
    """
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    access_token = serializers.CharField(required=False)
    refresh_token = serializers.CharField(required=False)
    user = UtilisateurSerializer(required=False)
    is_new_user = serializers.BooleanField(default=False)
    errors = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


# ============================================================================
# SÉRIALIZER POUR LES SERVICES
# ============================================================================

class ServiceSerializer(serializers.Serializer):
    """
    Sérializer pour les services administratifs.
    
    FIELDS:
        - id: Identifiant unique
        - nom: Nom du service
        - description: Description détaillée
        - delai_traitement_jours: Délai de traitement (SLA)
        - documents_requis: Liste des documents nécessaires
        - est_actif: Visibilité du service
        - ordre_affichage: Ordre dans les listes
        - tarif: Tarif du service
    """
    
    id = serializers.IntegerField(read_only=True)
    nom = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    delai_traitement_jours = serializers.IntegerField(min_value=1, default=7)
    documents_requis = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    est_actif = serializers.BooleanField(default=True)
    ordre_affichage = serializers.IntegerField(default=0)
    tarif = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
