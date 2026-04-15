"""
Package models pour l'application core.
Organisation modulaire des modèles avec POO avancée.
"""

from .exceptions import (
    CoreException,
    ValidationException,
    DemandeException,
    DocumentException,
    RDVException,
    AuthentificationException,
    PermissionException,
    NotificationException,
)

from .mixins import TimestampMixin, ProfilMixin, StatutMixin

from .utilisateur import UtilisateurManager, Utilisateur

from .profils import Citoyen, AgentAdministratif, Administrateur

from .demandes import ServiceAdministratif, DemandeAdministrative

from .documents import Document, Traitement

from .rdv import PropositionRDV, RendezVous

from .notifications import Notification

from .faq import FAQChatbot

__all__ = [
    # Exceptions
    'CoreException',
    'ValidationException',
    'DemandeException',
    'DocumentException',
    'RDVException',
    'AuthentificationException',
    'PermissionException',
    'NotificationException',
    # Mixins
    'TimestampMixin',
    'ProfilMixin',
    'StatutMixin',
    # Modèles principaux
    'UtilisateurManager',
    'Utilisateur',
    'Citoyen',
    'AgentAdministratif',
    'Administrateur',
    'ServiceAdministratif',
    'DemandeAdministrative',
    'Document',
    'Traitement',
    'PropositionRDV',
    'RendezVous',
    'Notification',
    'FAQChatbot',
]
