"""
================================================================================
MODULE: entities.py
COUCHE: Domain
RÔLE: Entités métier principales (Aggregates)

ARCHITECTURE:
    Entités = Objets avec identité unique et cycle de vie
    
    Utilisateur (Aggregate Root)
        └── Profil (Citoyen | Agent | Admin)
    
    Demande (Aggregate Root)
        ├── Documents (Value Objects)
        ├── Traitements (Entities)
        └── PropositionsRDV (Entities)

AGILE: Chaque entité correspond à une User Story ou Epic
================================================================================
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from .value_objects import Email, PhoneNumber, Address, Role, Status, DateRange
from .mixins import (
    TimestampMixin,
    SoftDeleteMixin,
    StatusMixin,
    AuditMixin,
    ValidatableMixin,
    WorkflowMixin
)


# ============================================================================
# ENTITÉ UTILISATEUR
# ============================================================================

@dataclass
class Utilisateur(TimestampMixin, SoftDeleteMixin, AuditMixin, ValidatableMixin):
    """
    Entité métier représentant un utilisateur du système.
    
    RÔLES:
        - CITOYEN: Soumission de demandes, consultation
        - AGENT: Traitement des demandes, propositions RDV
        - ADMINISTRATEUR: Gestion complète du système
    
    INVARIANTS:
        - Email unique et obligatoire
        - Rôle valide parmi les choix définis
        - Nom et prénom obligatoires
    
    EXEMPLE:
        >>> user = Utilisateur(
        ...     id=1,
        ...     email=Email("test@example.com"),
        ...     nom="DIOP",
        ...     prenom="Amadou",
        ...     telephone=PhoneNumber("77 123 45 67"),
        ...     role=Role.CITOYEN
        ... )
    """
    
    # Identité
    id: Optional[int] = field(default=None)
    
    # Authentification
    email: Email = field(default=None)
    password_hash: str = field(default="")
    
    # Profil
    nom: str = field(default="")
    prenom: str = field(default="")
    telephone: Optional[PhoneNumber] = field(default=None)
    
    # Rôle et permissions
    role: Role = field(default=Role.CITOYEN)
    is_active: bool = field(default=True)
    is_staff: bool = field(default=False)
    is_superuser: bool = field(default=False)
    
    # OAuth (optionnel)
    auth_provider: Optional[str] = field(default=None)  # 'google', 'facebook'
    social_id: Optional[str] = field(default=None)
    avatar_url: Optional[str] = field(default=None)
    
    # Relations (stockées comme IDs pour découplage)
    profile_id: Optional[int] = field(default=None)
    
    def validate(self) -> List[str]:
        """
        Valide les invariants métier de l'utilisateur.
        
        RETOURNE:
            Liste des messages d'erreur
        """
        errors = []
        
        if not self.nom or len(self.nom.strip()) < 2:
            errors.append("Le nom doit contenir au moins 2 caractères")
        
        if not self.prenom or len(self.prenom.strip()) < 2:
            errors.append("Le prénom doit contenir au moins 2 caractères")
        
        if not isinstance(self.email, Email):
            errors.append("Email invalide")
        
        if self.telephone and not isinstance(self.telephone, PhoneNumber):
            errors.append("Téléphone invalide")
        
        return errors
    
    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet formaté."""
        return f"{self.prenom} {self.nom}".strip()
    
    @property
    def is_citoyen(self) -> bool:
        """Vérifie si l'utilisateur est un citoyen."""
        return self.role == Role.CITOYEN
    
    @property
    def is_agent(self) -> bool:
        """Vérifie si l'utilisateur est un agent."""
        return self.role == Role.AGENT
    
    @property
    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur est un administrateur."""
        return self.role == Role.ADMINISTRATEUR
    
    def deactivate(self) -> None:
        """Désactive le compte utilisateur."""
        self.is_active = False
        self.touch()
    
    def activate(self) -> None:
        """Active le compte utilisateur."""
        self.is_active = True
        self.touch()
    
    def can_access(self, resource_owner_id: int) -> bool:
        """
        Vérifie si l'utilisateur peut accéder à une ressource.
        
        Un admin peut tout voir, un utilisateur ne voit que ses ressources.
        """
        if self.is_admin or self.is_staff:
            return True
        return self.id == resource_owner_id


@dataclass
class CitoyenProfile(TimestampMixin, ValidatableMixin):
    """
    Profil spécifique d'un citoyen.
    
    CONTIENT:
        - Informations personnelles complémentaires
        - Adresse
        - Documents d'identité
    """
    
    id: Optional[int] = field(default=None)
    utilisateur_id: int = field(default=0)
    
    # Informations personnelles
    date_naissance: Optional[date] = field(default=None)
    lieu_naissance: Optional[str] = field(default=None)
    cni_numero: Optional[str] = field(default=None)
    
    # Adresse
    adresse: Optional[Address] = field(default=None)
    
    # Statistiques
    total_demandes: int = field(default=0)
    demandes_en_cours: int = field(default=0)
    
    def validate(self) -> List[str]:
        """Validation du profil citoyen."""
        errors = []
        
        if self.cni_numero:
            if len(self.cni_numero) < 5:
                errors.append("Numéro CNI invalide")
        
        return errors


@dataclass
class AgentProfile(TimestampMixin):
    """
    Profil spécifique d'un agent administratif.
    
    CONTIENT:
        - Informations professionnelles
        - Service assigné
        - Disponibilité et charge de travail
    """
    
    id: Optional[int] = field(default=None)
    utilisateur_id: int = field(default=0)
    service_id: Optional[int] = field(default=None)
    
    # Informations professionnelles
    matricule: str = field(default="")
    date_embauche: Optional[date] = field(default=None)
    
    # Disponibilité
    est_disponible: bool = field(default=True)
    charge_actuelle: int = field(default=0)  # Nombre de demandes assignées
    
    # Compétences
    specialisations: List[str] = field(default_factory=list)
    
    def assigner_demande(self) -> None:
        """Incrémente la charge de travail."""
        self.charge_actuelle += 1
    
    def liberer_demande(self) -> None:
        """Décrémente la charge de travail."""
        if self.charge_actuelle > 0:
            self.charge_actuelle -= 1


# ============================================================================
# ENTITÉ DEMANDE ADMINISTRATIVE
# ============================================================================

@dataclass
class Demande(WorkflowMixin, TimestampMixin, AuditMixin, ValidatableMixin):
    """
    Entité métier représentant une demande administrative.
    
    WORKFLOW:
        brouillon → soumise → en_traitement → [traitee | rejetee] → archivee
                        ↓
                    en_attente (documents manquants)
    
    EXEMPLE:
        >>> demande = Demande(
        ...     id=1,
        ...     citoyen_id=123,
        ...     service_id=5,
        ...     titre="Demande d'acte de naissance"
        ... )
        >>> demande.transition_to('soumise', changed_by='citoyen@example.com')
    """
    
    # Workflow autorisé
    ALLOWED_TRANSITIONS: Dict[str, List[str]] = field(default_factory=lambda: {
        'brouillon': ['soumise'],
        'soumise': ['en_traitement', 'rejetee'],
        'en_traitement': ['en_attente', 'traitee', 'rejetee'],
        'en_attente': ['en_traitement', 'rejetee'],
        'traitee': ['archivee'],
        'rejetee': ['archivee'],
        'archivee': []
    })
    
    # Identité
    id: Optional[int] = field(default=None)
    numero_reference: str = field(default="")  # Ex: DEM-2024-000123
    
    # Relations
    citoyen_id: int = field(default=0)
    service_id: int = field(default=0)
    agent_id: Optional[int] = field(default=None)  # Agent assigné
    
    # Contenu
    titre: str = field(default="")
    description: str = field(default="")
    type_document: str = field(default="")  # 'acte_naissance', 'acte_mariage', etc.
    
    # Statut (hérité de WorkflowMixin)
    status: str = field(default="brouillon")
    
    # Dates importantes
    date_soumission: Optional[datetime] = field(default=None)
    date_debut_traitement: Optional[datetime] = field(default=None)
    date_cloture: Optional[datetime] = field(default=None)
    date_echeance: Optional[datetime] = field(default=None)  # SLA
    
    # Priorité
    priorite: str = field(default="normal")  # 'basse', 'normal', 'haute', 'urgente'
    
    # Compléments
    notes_internes: str = field(default="")
    motif_rejet: Optional[str] = field(default=None)
    
    def validate(self) -> List[str]:
        """Validation de la demande."""
        errors = []
        
        if not self.titre or len(self.titre) < 5:
            errors.append("Le titre doit contenir au moins 5 caractères")
        
        if not self.service_id:
            errors.append("Un service doit être sélectionné")
        
        if not self.citoyen_id:
            errors.append("Un citoyen doit être associé")
        
        return errors
    
    def soumettre(self) -> None:
        """Soumet la demande pour traitement."""
        self.transition_to('soumise')
        self.date_soumission = datetime.now()
        self.touch()
    
    def assigner_agent(self, agent_id: int) -> None:
        """Assigne un agent à la demande."""
        self.agent_id = agent_id
        self.transition_to('en_traitement')
        self.date_debut_traitement = datetime.now()
        self.touch()
    
    def demander_complement(self, motif: str) -> None:
        """Met la demande en attente pour documents manquants."""
        self.transition_to('en_attente', reason=motif)
        self.notes_internes += f"\n[{datetime.now()}] Complément demandé: {motif}"
        self.touch()
    
    def traiter(self) -> None:
        """Marque la demande comme traitée."""
        self.transition_to('traitee')
        self.date_cloture = datetime.now()
        self.touch()
    
    def rejeter(self, motif: str) -> None:
        """Rejette la demande avec un motif."""
        self.transition_to('rejetee', reason=motif)
        self.motif_rejet = motif
        self.date_cloture = datetime.now()
        self.touch()
    
    @property
    def is_overdue(self) -> bool:
        """Vérifie si la demande dépasse l'échéance."""
        if self.date_echeance and self.status not in ['traitee', 'rejetee', 'archivee']:
            return datetime.now() > self.date_echeance
        return False
    
    @property
    def duree_traitement(self) -> Optional[int]:
        """Retourne la durée de traitement en jours."""
        if self.date_debut_traitement and self.date_cloture:
            return (self.date_cloture - self.date_debut_traitement).days
        if self.date_debut_traitement:
            return (datetime.now() - self.date_debut_traitement).days
        return None


# ============================================================================
# ENTITÉS SUPPORT
# ============================================================================

@dataclass
class Document(TimestampMixin, AuditMixin):
    """
    Document associé à une demande.
    
    TYPES:
        - piece_identite: CNI, Passeport
        - justificatif: Facture, Contrat
        - formulaire: Formulaire administratif
        - attestation: Attestation officielle
    """
    
    id: Optional[int] = field(default=None)
    demande_id: int = field(default=0)
    uploaded_by_id: int = field(default=0)
    
    # Fichier
    fichier_nom: str = field(default="")
    fichier_chemin: str = field(default="")
    fichier_type: str = field(default="")  # MIME type
    fichier_taille: int = field(default=0)  # octets
    
    # Métadonnées
    type_document: str = field(default="")  # categorie
    description: Optional[str] = field(default=None)
    est_verifie: bool = field(default=False)
    
    @property
    def taille_readable(self) -> str:
        """Retourne la taille lisible (KB, MB)."""
        if self.fichier_taille < 1024:
            return f"{self.fichier_taille} o"
        elif self.fichier_taille < 1024 * 1024:
            return f"{self.fichier_taille / 1024:.1f} Ko"
        else:
            return f"{self.fichier_taille / (1024 * 1024):.1f} Mo"


@dataclass
class Traitement(TimestampMixin):
    """
    Action de traitement effectuée sur une demande.
    
    ACTIONS:
        - creation: Demande créée
        - verification: Documents vérifiés
        - assignation: Assignée à un agent
        - complement: Demande de complément
        - validation: Demande validée
        - rejet: Demande rejetée
        - cloture: Demande clôturée
    """
    
    id: Optional[int] = field(default=None)
    demande_id: int = field(default=0)
    agent_id: int = field(default=0)
    
    action: str = field(default="")  # Type d'action
    commentaire: str = field(default="")
    
    # État avant/après
    statut_precedent: Optional[str] = field(default=None)
    nouveau_statut: Optional[str] = field(default=None)


@dataclass
class RendezVous(TimestampMixin, WorkflowMixin, ValidatableMixin):
    """
    Rendez-vous entre citoyen et agent.
    
    WORKFLOW:
        propose → confirme → realise
            ↓
        annule
    """
    
    ALLOWED_TRANSITIONS: Dict[str, List[str]] = field(default_factory=lambda: {
        'propose': ['confirme', 'annule'],
        'confirme': ['realise', 'non_honore', 'annule'],
        'realise': [],
        'non_honore': [],
        'annule': []
    })
    
    id: Optional[int] = field(default=None)
    demande_id: int = field(default=0)
    citoyen_id: int = field(default=0)
    agent_id: int = field(default=0)
    
    # Date et heure
    date_rdv: date = field(default_factory=date.today)
    heure_debut: str = field(default="09:00")
    heure_fin: str = field(default="10:00")
    
    # Détails
    lieu: str = field(default="")
    motif: str = field(default="")
    
    # Statut
    status: str = field(default="propose")
    
    # Confirmation
    date_confirmation: Optional[datetime] = field(default=None)
    date_annulation: Optional[datetime] = field(default=None)
    
    def confirmer(self) -> None:
        """Confirme le rendez-vous par le citoyen."""
        self.transition_to('confirme')
        self.date_confirmation = datetime.now()
    
    def annuler(self, motif: str = "") -> None:
        """Annule le rendez-vous."""
        self.transition_to('annule', reason=motif)
        self.date_annulation = datetime.now()
    
    def marquer_realise(self) -> None:
        """Marque le rendez-vous comme effectué."""
        self.transition_to('realise')
    
    def validate(self) -> List[str]:
        """Validation du rendez-vous."""
        errors = []
        
        if not self.lieu:
            errors.append("Le lieu est obligatoire")
        
        if self.heure_fin <= self.heure_debut:
            errors.append("L'heure de fin doit être après l'heure de début")
        
        return errors


@dataclass
class Service(TimestampMixin, ValidatableMixin):
    """
    Service administratif proposé.
    
    EXEMPLES:
        - État Civil (actes de naissance, mariage, décès)
        - Urbanisme (permis de construire)
        - Finances (paiement taxes)
    """
    
    id: Optional[int] = field(default=None)
    
    nom: str = field(default="")
    description: str = field(default="")
    
    # Configuration
    delai_traitement_jours: int = field(default=7)
    documents_requis: List[str] = field(default_factory=list)
    
    # État
    est_actif: bool = field(default=True)
    ordre_affichage: int = field(default=0)
    
    # Tarification (optionnel)
    tarif: Decimal = field(default_factory=lambda: Decimal("0.00"))
    
    def validate(self) -> List[str]:
        """Validation du service."""
        errors = []
        
        if not self.nom or len(self.nom) < 3:
            errors.append("Le nom doit contenir au moins 3 caractères")
        
        if self.delai_traitement_jours < 1:
            errors.append("Le délai de traitement doit être d'au moins 1 jour")
        
        return errors


@dataclass
class Notification(TimestampMixin):
    """
    Notification envoyée à un utilisateur.
    
    TYPES:
        - info: Information générale
        - success: Action réussie
        - warning: Attention requise
        - error: Erreur à corriger
    """
    
    id: Optional[int] = field(default=None)
    destinataire_id: int = field(default=0)
    
    # Contenu
    type_notification: str = field(default="info")  # info, success, warning, error
    titre: str = field(default="")
    message: str = field(default="")
    
    # Liens
    demande_id: Optional[int] = field(default=None)
    lien_action: Optional[str] = field(default=None)  # URL vers la ressource
    
    # État
    is_read: bool = field(default=False)
    date_lecture: Optional[datetime] = field(default=None)
    
    def marquer_lu(self) -> None:
        """Marque la notification comme lue."""
        self.is_read = True
        self.date_lecture = datetime.now()


@dataclass
class FAQEntry(TimestampMixin):
    """
    Entrée FAQ pour le chatbot.
    """
    
    id: Optional[int] = field(default=None)
    
    question: str = field(default="")
    reponse: str = field(default="")
    categorie: str = field(default="general")
    
    # Recherche
    mots_cles: List[str] = field(default_factory=list)
    compteur_utilisation: int = field(default=0)
    
    def incrementer_utilisation(self) -> None:
        """Incrémente le compteur d'utilisation."""
        self.compteur_utilisation += 1
