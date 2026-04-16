"""
================================================================================
MODULE: dtos.py
COUCHE: Application
RÔLE: Data Transfer Objects - Objets de transfert de données

ARCHITECTURE:
    Les DTOs découplent les entités du format de transport.
    Ils définissent explicitement les données entrantes/sortantes.

    Input DTOs: Données reçues de l'extérieur (API)
    Output DTOs: Données retournées (API responses)

PATTERN: Data Transfer Object (DTO) Pattern
AGILE: DTOs = API Contracts pour chaque User Story
================================================================================
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from ..domain.value_objects import Role, Status


# ============================================================================
# BASE DTO
# ============================================================================

@dataclass
class BaseInputDTO:
    """
    Classe base pour les DTOs d'entrée.
    
    FOURNIT:
        - Validation automatique
        - Conversion vers entité
    """
    
    def validate(self) -> List[str]:
        """
        Valide les données d'entrée.
        
        RETOURNE:
            Liste des erreurs (vide si valide)
        """
        return []
    
    def is_valid(self) -> bool:
        """Vérifie si le DTO est valide."""
        return len(self.validate()) == 0


@dataclass
class BaseOutputDTO:
    """
    Classe base pour les DTOs de sortie.
    
    FOURNIT:
        - Sérialisation automatique
        - Métadonnées de réponse
    """
    
    success: bool = True
    message: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le DTO en dictionnaire."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, date):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


# ============================================================================
# AUTH DTOs
# ============================================================================

@dataclass
class RegisterInputDTO(BaseInputDTO):
    """
    DTO pour l'inscription d'un utilisateur.
    
    EXEMPLE:
        >>> input_dto = RegisterInputDTO(
        ...     email="test@example.com",
        ...     password="SecurePass123",
        ...     password_confirm="SecurePass123",
        ...     nom="DIOP",
        ...     prenom="Amadou",
        ...     telephone="77 123 45 67"
        ... )
    """
    
    email: str = ""
    password: str = ""
    password_confirm: str = ""
    nom: str = ""
    prenom: str = ""
    telephone: str = ""
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.email or '@' not in self.email:
            errors.append("Email invalide")
        
        if len(self.password) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères")
        
        if self.password != self.password_confirm:
            errors.append("Les mots de passe ne correspondent pas")
        
        if len(self.nom) < 2:
            errors.append("Le nom doit contenir au moins 2 caractères")
        
        if len(self.prenom) < 2:
            errors.append("Le prénom doit contenir au moins 2 caractères")
        
        return errors


@dataclass
class LoginInputDTO(BaseInputDTO):
    """DTO pour la connexion."""
    
    email: str = ""
    password: str = ""
    
    def validate(self) -> List[str]:
        errors = []
        if not self.email:
            errors.append("Email requis")
        if not self.password:
            errors.append("Mot de passe requis")
        return errors


@dataclass
class OAuthInputDTO(BaseInputDTO):
    """DTO pour l'authentification OAuth."""
    
    provider: str = ""  # 'google', 'facebook'
    access_token: str = ""
    
    def validate(self) -> List[str]:
        errors = []
        if self.provider not in ['google', 'facebook']:
            errors.append("Provider OAuth non supporté")
        if not self.access_token:
            errors.append("Token d'accès requis")
        return errors


@dataclass
class AuthOutputDTO(BaseOutputDTO):
    """DTO de sortie pour l'authentification."""
    
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional['UserDTO'] = None
    is_new_user: bool = False


# ============================================================================
# USER DTOs
# ============================================================================

@dataclass
class UserDTO(BaseOutputDTO):
    """
    DTO pour représenter un utilisateur.
    
    Utilisé dans les réponses API.
    """
    
    id: int = 0
    email: str = ""
    nom: str = ""
    prenom: str = ""
    telephone: str = ""
    role: str = ""
    role_display: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    avatar_url: Optional[str] = None
    
    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet."""
        return f"{self.prenom} {self.nom}".strip()


@dataclass
class UserUpdateInputDTO(BaseInputDTO):
    """DTO pour la mise à jour d'un utilisateur."""
    
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    
    def validate(self) -> List[str]:
        errors = []
        if self.nom and len(self.nom) < 2:
            errors.append("Le nom doit contenir au moins 2 caractères")
        if self.prenom and len(self.prenom) < 2:
            errors.append("Le prénom doit contenir au moins 2 caractères")
        return errors


@dataclass
class ChangePasswordInputDTO(BaseInputDTO):
    """DTO pour changer le mot de passe."""
    
    current_password: str = ""
    new_password: str = ""
    new_password_confirm: str = ""
    
    def validate(self) -> List[str]:
        errors = []
        if len(self.new_password) < 8:
            errors.append("Le nouveau mot de passe doit contenir au moins 8 caractères")
        if self.new_password != self.new_password_confirm:
            errors.append("Les mots de passe ne correspondent pas")
        return errors


# ============================================================================
# DEMANDE DTOs
# ============================================================================

@dataclass
class CreateDemandeInputDTO(BaseInputDTO):
    """
    DTO pour créer une demande administrative.
    
    EXEMPLE:
        >>> dto = CreateDemandeInputDTO(
        ...     service_id=5,
        ...     titre="Demande d'acte de naissance",
        ...     description="Acte pour mon fils",
        ...     type_document="acte_naissance"
        ... )
    """
    
    service_id: int = 0
    titre: str = ""
    description: str = ""
    type_document: str = ""
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.service_id:
            errors.append("Un service doit être sélectionné")
        
        if len(self.titre) < 5:
            errors.append("Le titre doit contenir au moins 5 caractères")
        
        if len(self.description) < 10:
            errors.append("La description doit contenir au moins 10 caractères")
        
        return errors


@dataclass
class UpdateDemandeInputDTO(BaseInputDTO):
    """DTO pour modifier une demande (brouillon uniquement)."""
    
    titre: Optional[str] = None
    description: Optional[str] = None
    
    def validate(self) -> List[str]:
        errors = []
        if self.titre and len(self.titre) < 5:
            errors.append("Le titre doit contenir au moins 5 caractères")
        return errors


@dataclass
class DemandeDTO(BaseOutputDTO):
    """DTO pour représenter une demande."""
    
    id: int = 0
    numero_reference: str = ""
    
    # Relations
    citoyen_id: int = 0
    citoyen_nom: str = ""
    service_id: int = 0
    service_nom: str = ""
    agent_id: Optional[int] = None
    agent_nom: Optional[str] = None
    
    # Contenu
    titre: str = ""
    description: str = ""
    type_document: str = ""
    
    # Statut
    status: str = ""
    status_display: str = ""
    
    # Dates
    created_at: Optional[datetime] = None
    date_soumission: Optional[datetime] = None
    date_debut_traitement: Optional[datetime] = None
    date_cloture: Optional[datetime] = None
    date_echeance: Optional[datetime] = None
    
    # Métadonnées
    priorite: str = ""
    is_overdue: bool = False
    duree_traitement: Optional[int] = None  # jours
    
    # Historique
    status_history: List[Dict] = field(default_factory=list)
    
    # Documents
    documents: List['DocumentDTO'] = field(default_factory=list)


@dataclass
class AssignDemandeInputDTO(BaseInputDTO):
    """DTO pour assigner une demande à un agent."""
    
    agent_id: int = 0
    
    def validate(self) -> List[str]:
        errors = []
        if not self.agent_id:
            errors.append("Un agent doit être sélectionné")
        return errors


@dataclass
class StatusChangeInputDTO(BaseInputDTO):
    """DTO pour changer le statut d'une demande."""
    
    new_status: str = ""
    reason: Optional[str] = None
    
    def validate(self) -> List[str]:
        errors = []
        valid_statuses = [
            'brouillon', 'soumise', 'en_traitement', 'en_attente',
            'traitee', 'rejetee', 'archivee'
        ]
        if self.new_status not in valid_statuses:
            errors.append(f"Statut invalide. Valeurs possibles: {valid_statuses}")
        return errors


# ============================================================================
# DOCUMENT DTOs
# ============================================================================

@dataclass
class UploadDocumentInputDTO(BaseInputDTO):
    """DTO pour uploader un document."""
    
    demande_id: int = 0
    type_document: str = ""
    description: Optional[str] = None
    fichier_nom: str = ""
    fichier_taille: int = 0
    fichier_content_type: str = ""
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.demande_id:
            errors.append("Une demande doit être spécifiée")
        
        if not self.type_document:
            errors.append("Le type de document est requis")
        
        max_size = 10 * 1024 * 1024  # 10 MB
        if self.fichier_taille > max_size:
            errors.append("Le fichier ne doit pas dépasser 10 Mo")
        
        valid_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/jpg'
        ]
        if self.fichier_content_type not in valid_types:
            errors.append("Format non supporté (PDF, JPEG, PNG uniquement)")
        
        return errors


@dataclass
class DocumentDTO(BaseOutputDTO):
    """DTO pour représenter un document."""
    
    id: int = 0
    demande_id: int = 0
    
    # Fichier
    fichier_nom: str = ""
    fichier_url: str = ""
    fichier_type: str = ""
    fichier_taille: int = 0
    taille_readable: str = ""
    
    # Métadonnées
    type_document: str = ""
    type_display: str = ""
    description: Optional[str] = None
    est_verifie: bool = False
    
    # Dates
    created_at: Optional[datetime] = None
    uploaded_by_nom: str = ""


# ============================================================================
# RDV DTOs
# ============================================================================

@dataclass
class CreateRDVInputDTO(BaseInputDTO):
    """DTO pour créer une proposition de RDV."""
    
    demande_id: int = 0
    date_rdv: str = ""  # Format: YYYY-MM-DD
    heure_debut: str = ""  # Format: HH:MM
    heure_fin: str = ""  # Format: HH:MM
    lieu: str = ""
    motif: str = ""
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.demande_id:
            errors.append("Une demande doit être spécifiée")
        
        if not self.date_rdv:
            errors.append("La date est requise")
        
        if not self.lieu:
            errors.append("Le lieu est requis")
        
        if self.heure_fin <= self.heure_debut:
            errors.append("L'heure de fin doit être après l'heure de début")
        
        return errors


@dataclass
class RDVDTO(BaseOutputDTO):
    """DTO pour représenter un rendez-vous."""
    
    id: int = 0
    demande_id: int = 0
    
    # Participants
    citoyen_id: int = 0
    citoyen_nom: str = ""
    agent_id: int = 0
    agent_nom: str = ""
    
    # Date/Heure
    date_rdv: Optional[date] = None
    heure_debut: str = ""
    heure_fin: str = ""
    
    # Détails
    lieu: str = ""
    motif: str = ""
    status: str = ""
    status_display: str = ""
    
    # Dates système
    created_at: Optional[datetime] = None
    date_confirmation: Optional[datetime] = None


@dataclass
class ConfirmerRDVInputDTO(BaseInputDTO):
    """DTO pour confirmer un RDV."""
    
    rdv_id: int = 0
    
    def validate(self) -> List[str]:
        errors = []
        if not self.rdv_id:
            errors.append("Un RDV doit être spécifié")
        return errors


# ============================================================================
# NOTIFICATION DTOs
# ============================================================================

@dataclass
class NotificationDTO(BaseOutputDTO):
    """DTO pour représenter une notification."""
    
    id: int = 0
    type_notification: str = ""
    titre: str = ""
    message: str = ""
    
    is_read: bool = False
    created_at: Optional[datetime] = None
    date_lecture: Optional[datetime] = None
    
    demande_id: Optional[int] = None
    lien_action: Optional[str] = None


@dataclass
class CreateNotificationInputDTO(BaseInputDTO):
    """DTO pour créer une notification."""
    
    destinataire_id: int = 0
    type_notification: str = ""
    titre: str = ""
    message: str = ""
    demande_id: Optional[int] = None
    lien_action: Optional[str] = None
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.destinataire_id:
            errors.append("Un destinataire est requis")
        
        valid_types = ['info', 'success', 'warning', 'error']
        if self.type_notification not in valid_types:
            errors.append(f"Type invalide. Valeurs possibles: {valid_types}")
        
        return errors


# ============================================================================
# SERVICE DTOs
# ============================================================================

@dataclass
class ServiceDTO(BaseOutputDTO):
    """DTO pour représenter un service administratif."""
    
    id: int = 0
    nom: str = ""
    description: str = ""
    delai_traitement_jours: int = 0
    documents_requis: List[str] = field(default_factory=list)
    est_actif: bool = True
    tarif: float = 0.0


# ============================================================================
# PAGINATION & LIST DTOs
# ============================================================================

@dataclass
class PaginationInputDTO(BaseInputDTO):
    """DTO pour la pagination."""
    
    page: int = 1
    page_size: int = 20
    
    def validate(self) -> List[str]:
        errors = []
        if self.page < 1:
            errors.append("La page doit être >= 1")
        if self.page_size < 1 or self.page_size > 100:
            errors.append("La taille de page doit être entre 1 et 100")
        return errors
    
    @property
    def offset(self) -> int:
        """Calcule l'offset pour la requête SQL."""
        return (self.page - 1) * self.page_size


@dataclass
class PaginatedOutputDTO(BaseOutputDTO):
    """DTO pour les réponses paginées."""
    
    items: List[Any] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    
    has_next: bool = False
    has_previous: bool = False
    
    @property
    def next_page(self) -> Optional[int]:
        """Numéro de la page suivante."""
        return self.page + 1 if self.has_next else None
    
    @property
    def previous_page(self) -> Optional[int]:
        """Numéro de la page précédente."""
        return self.page - 1 if self.has_previous else None
