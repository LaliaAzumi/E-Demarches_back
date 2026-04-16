"""
================================================================================
MODULE: value_objects.py
COUCHE: Domain
RÔLE: Objets de valeur immuables et validés

ARCHITECTURE:
    Les Value Objects encapsulent des concepts métier avec validation:
    - Email: Validation format email
    - PhoneNumber: Validation format téléphone
    - Address: Structure d'adresse
    - Status: Énumération des statuts
    - Role: Énumération des rôles
    - DateRange: Période temporelle

PRINCIPE: Immuabilité - une fois créé, l'objet ne change pas
AGILE: Value Objects = Concepts métier partagés entre User Stories
================================================================================
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional, List
from enum import Enum


@dataclass(frozen=True)
class Email:
    """
    Objet de valeur représentant une adresse email validée.
    
    ATTIBUTS:
        value (str): L'email normalisé (minuscules, sans espaces)
    
    EXEMPLE:
        >>> email = Email("Test@Example.com")
        >>> print(email.value)  # "test@example.com"
        >>> print(email.domain)  # "example.com"
    
    LÈVE:
        ValueError: Si le format email est invalide
    """
    
    value: str
    
    def __post_init__(self):
        """Validation du format email après création."""
        # Normalisation
        normalized = self.value.lower().strip()
        
        # Regex pour validation email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, normalized):
            raise ValueError(f"Format email invalide: {self.value}")
        
        # Modification via object.__setattr__ car frozen=True
        object.__setattr__(self, 'value', normalized)
    
    @property
    def domain(self) -> str:
        """Extrait le domaine de l'email."""
        return self.value.split('@')[1]
    
    @property
    def username(self) -> str:
        """Extrait la partie locale de l'email."""
        return self.value.split('@')[0]
    
    def __str__(self) -> str:
        """Représentation string."""
        return self.value
    
    def __eq__(self, other) -> bool:
        """Comparaison basée sur la valeur."""
        if not isinstance(other, Email):
            return False
        return self.value == other.value


@dataclass(frozen=True)
class PhoneNumber:
    """
    Objet de valeur représentant un numéro de téléphone validé.
    
    Supporte les formats:
    - Local (sénégalais): 77 XXX XX XX, 76 XXX XX XX, etc.
    - International: +221 77 XXX XX XX
    
    EXEMPLE:
        >>> phone = PhoneNumber("77 123 45 67")
        >>> print(phone.formatted)  # "+221 77 123 45 67"
        >>> print(phone.is_local)   # True
    
    LÈVE:
        ValueError: Si le format téléphone est invalide
    """
    
    value: str
    
    def __post_init__(self):
        """Validation et normalisation du numéro."""
        # Supprimer tous les espaces et caractères non numériques sauf +
        cleaned = re.sub(r'[\s.-]', '', self.value)
        
        # Supprimer le préfixe +221 ou 00221 s'il existe
        if cleaned.startswith('+221'):
            cleaned = cleaned[4:]
        elif cleaned.startswith('00221'):
            cleaned = cleaned[5:]
        
        # Validation: doit commencer par 7 et avoir 9 chiffres (Sénégal)
        if not re.match(r'^7[0-8]\d{7}$', cleaned):
            raise ValueError(
                f"Format téléphone invalide: {self.value}. "
                "Format attendu: 77 XXX XX XX ou +221 77 XXX XX XX"
            )
        
        object.__setattr__(self, 'value', cleaned)
    
    @property
    def formatted(self) -> str:
        """Retourne le numéro formaté avec indicatif."""
        return f"+221 {self.value[:2]} {self.value[2:5]} {self.value[5:7]} {self.value[7:9]}"
    
    @property
    def local_format(self) -> str:
        """Retourne le numéro formaté local."""
        return f"{self.value[:2]} {self.value[2:5]} {self.value[5:7]} {self.value[7:9]}"
    
    @property
    def operator(self) -> str:
        """Détecte l'opérateur téléphonique."""
        prefix = self.value[:2]
        operators = {
            '77': 'Orange',
            '78': 'Orange', 
            '76': 'Free',
            '70': 'Expresso',
            '75': 'Promobile'
        }
        return operators.get(prefix, 'Inconnu')
    
    def __str__(self) -> str:
        return self.formatted


@dataclass(frozen=True)
class Address:
    """
    Objet de valeur représentant une adresse postale structurée.
    
    EXEMPLE:
        >>> addr = Address(
        ...     street="123 Rue de Dakar",
        ...     city="Dakar",
        ...     postal_code="10000"
        ... )
        >>> print(addr.full_address)
    
    ATTRIBUTS:
        street: Rue et numéro
        city: Ville
        postal_code: Code postal
        country: Pays (défaut: Sénégal)
    """
    
    street: str
    city: str
    postal_code: str
    country: str = field(default="Sénégal")
    
    def __post_init__(self):
        """Nettoyage des valeurs."""
        object.__setattr__(self, 'street', self.street.strip())
        object.__setattr__(self, 'city', self.city.strip().title())
        object.__setattr__(self, 'postal_code', self.postal_code.strip())
    
    @property
    def full_address(self) -> str:
        """Adresse complète formatée sur plusieurs lignes."""
        return f"{self.street}\n{self.postal_code} {self.city}\n{self.country}"
    
    @property
    def one_line(self) -> str:
        """Adresse sur une seule ligne."""
        return f"{self.street}, {self.postal_code} {self.city}"


class Status(Enum):
    """
    Énumération des statuts possibles pour les entités métier.
    
    UTILISATION:
        Les statuts sont organisés par catégorie d'entité:
        - Utilisateur: ACTIVE, INACTIVE, SUSPENDED
        - Demande: DRAFT, SUBMITTED, IN_PROGRESS, COMPLETED, REJECTED
        - RDV: PROPOSED, CONFIRMED, COMPLETED, CANCELLED
    """
    
    # Statuts utilisateur
    USER_ACTIVE = "active"
    USER_INACTIVE = "inactive"
    USER_SUSPENDED = "suspended"
    
    # Statuts demande administrative
    DEMANDE_DRAFT = "brouillon"
    DEMANDE_SUBMITTED = "soumise"
    DEMANDE_IN_PROGRESS = "en_traitement"
    DEMANDE_WAITING = "en_attente"
    DEMANDE_COMPLETED = "traitee"
    DEMANDE_REJECTED = "rejetee"
    DEMANDE_ARCHIVED = "archivee"
    
    # Statuts rendez-vous
    RDV_PROPOSED = "propose"
    RDV_CONFIRMED = "confirme"
    RDV_COMPLETED = "realise"
    RDV_CANCELLED = "annule"
    RDV_NO_SHOW = "non_honore"


class Role(Enum):
    """
    Énumération des rôles utilisateur dans le système.
    
    HIERARCHIE:
        1. ADMINISTRATEUR (Administrator): Gestion complète du système
        2. AGENT (Agent): Traitement des demandes
        3. CITOYEN (Citizen): Soumission de demandes
    
    EXEMPLE:
        >>> if user.role == Role.AGENT:
        ...     # Actions réservées aux agents
    """
    
    CITOYEN = "citoyen"
    AGENT = "agent"
    ADMINISTRATEUR = "administrateur"
    
    @classmethod
    def get_choices(cls) -> List[tuple]:
        """Retourne les choix pour Django CharField.choices."""
        return [
            (cls.CITOYEN.value, "Citoyen"),
            (cls.AGENT.value, "Agent administratif"),
            (cls.ADMINISTRATEUR.value, "Administrateur"),
        ]
    
    @property
    def label(self) -> str:
        """Label humain du rôle."""
        labels = {
            self.CITOYEN: "Citoyen",
            self.AGENT: "Agent administratif",
            self.ADMINISTRATEUR: "Administrateur",
        }
        return labels[self]


@dataclass(frozen=True)
class DateRange:
    """
    Objet de valeur représentant une plage de dates.
    
    UTILE POUR:
        - Périodes de disponibilité
        - Durées de traitement
        - Recherche par date
    
    EXEMPLE:
        >>> range = DateRange(
        ...     start=date(2024, 1, 1),
        ...     end=date(2024, 12, 31)
        ... )
        >>> print(range.duration_days)  # 365
        >>> print(range.contains(date(2024, 6, 15)))  # True
    
    LÈVE:
        ValueError: Si start > end
    """
    
    start: date
    end: date
    
    def __post_init__(self):
        """Validation de la cohérence des dates."""
        if self.start > self.end:
            raise ValueError(
                f"Date de début ({self.start}) doit être <= date de fin ({self.end})"
            )
    
    @property
    def duration_days(self) -> int:
        """Nombre de jours dans la plage."""
        return (self.end - self.start).days
    
    @property
    def is_past(self) -> bool:
        """Vérifie si la plage est entièrement dans le passé."""
        return self.end < date.today()
    
    @property
    def is_current(self) -> bool:
        """Vérifie si aujourd'hui est dans la plage."""
        today = date.today()
        return self.start <= today <= self.end
    
    @property
    def is_future(self) -> bool:
        """Vérifie si la plage est entièrement dans le futur."""
        return self.start > date.today()
    
    def contains(self, check_date: date) -> bool:
        """Vérifie si une date est dans la plage."""
        return self.start <= check_date <= self.end
    
    def overlaps(self, other: 'DateRange') -> bool:
        """Vérifie le chevauchement avec une autre plage."""
        return (
            self.contains(other.start) or 
            self.contains(other.end) or
            other.contains(self.start)
        )
    
    def __str__(self) -> str:
        return f"{self.start} → {self.end} ({self.duration_days} jours)"
