"""
================================================================================
MODULE: external_services.py
COUCHE: Infrastructure
RÔLE: Interfaces pour les services externes

ARCHITECTURE:
    Définit les contrats (interfaces) pour:
    - Envoi d'emails
    - Authentification OAuth
    - Stockage de fichiers
    - Notifications push

PATTERN: Adapter Pattern - Abstraction des services externes
AGILE: External Services = Integration Stories
================================================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, BinaryIO, Any

from ..domain.value_objects import Email


# ============================================================================
# EMAIL SERVICE
# ============================================================================

@dataclass
class EmailMessage:
    """
    Objet représentant un email à envoyer.
    
    ATTRIBUTS:
        to: Liste des destinataires
        subject: Sujet
        body: Corps texte
        html_body: Corps HTML (optionnel)
        from_email: Expéditeur
        attachments: Pièces jointes
    """
    to: List[Email]
    subject: str
    body: str
    html_body: Optional[str] = None
    from_email: Optional[Email] = None
    attachments: List[Dict] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []


class EmailServiceInterface(ABC):
    """
    Interface pour le service d'envoi d'emails.
    
    IMPLEMENTATIONS POSSIBLES:
        - SMTP (Django)
        - SendGrid
        - Mailgun
        - AWS SES
    
    EXEMPLE:
        >>> email_service = DjangoEmailService()
        >>> message = EmailMessage(
        ...     to=[Email("user@example.com")],
        ...     subject="Confirmation",
        ...     body="Votre demande a été reçue"
        ... )
        >>> email_service.send(message)
    """
    
    @abstractmethod
    def send(self, message: EmailMessage) -> bool:
        """
        Envoie un email.
        
        PARAMÈTRES:
            message: Email à envoyer
            
        RETOURNE:
            True si envoyé avec succès
        """
        pass
    
    @abstractmethod
    def send_template(self, to: List[Email], template_id: str,
                     context: Dict) -> bool:
        """
        Envoie un email basé sur un template.
        
        PARAMÈTRES:
            to: Destinataires
            template_id: ID du template
            context: Variables du template
        """
        pass
    
    @abstractmethod
    def send_bulk(self, messages: List[EmailMessage]) -> Dict[Email, bool]:
        """
        Envoie plusieurs emails en batch.
        
        RETOURNE:
            Dict indiquant le succès par destinataire
        """
        pass


# ============================================================================
# OAUTH SERVICE
# ============================================================================

@dataclass
class OAuthUserInfo:
    """
    Informations utilisateur retournées par OAuth.
    
    ATTRIBUTS:
        provider: Provider OAuth ('google', 'facebook')
        social_id: ID unique chez le provider
        email: Email vérifié
        first_name: Prénom
        last_name: Nom
        picture_url: URL avatar
        is_verified: Email vérifié
    """
    provider: str
    social_id: str
    email: Email
    first_name: str
    last_name: str
    picture_url: Optional[str] = None
    is_verified: bool = False


class OAuthServiceInterface(ABC):
    """
    Interface pour l'authentification OAuth.
    
    IMPLEMENTATIONS:
        - Google OAuth 2.0
        - Facebook Login
        - Microsoft Identity
    
    EXEMPLE:
        >>> oauth = GoogleOAuthService()
        >>> user_info = oauth.verify_token(access_token)
        >>> if user_info:
        ...     # Créer ou connecter l'utilisateur
    """
    
    @abstractmethod
    def verify_token(self, access_token: str) -> Optional[OAuthUserInfo]:
        """
        Vérifie un token d'accès OAuth.
        
        PARAMÈTRES:
            access_token: Token fourni par le client
            
        RETOURNE:
            Informations utilisateur ou None si invalide
        """
        pass
    
    @abstractmethod
    def get_authorization_url(self, redirect_uri: str,
                              state: Optional[str] = None) -> str:
        """
        Génère l'URL d'autorisation OAuth.
        
        PARAMÈTRES:
            redirect_uri: URL de redirection
            state: Paramètre anti-CSRF
            
        RETOURNE:
            URL complète d'autorisation
        """
        pass
    
    @abstractmethod
    def exchange_code(self, code: str, redirect_uri: str) -> Optional[str]:
        """
        Échange un code d'autorisation contre un token.
        
        PARAMÈTRES:
            code: Code d'autorisation
            redirect_uri: Même URL de redirection
            
        RETOURNE:
            Access token ou None
        """
        pass


# ============================================================================
# FILE STORAGE SERVICE
# ============================================================================

class FileStorageInterface(ABC):
    """
    Interface pour le stockage de fichiers.
    
    IMPLEMENTATIONS:
        - Local filesystem
        - AWS S3
        - Google Cloud Storage
        - Azure Blob Storage
    
    EXEMPLE:
        >>> storage = S3StorageService()
        >>> path = storage.save('documents/acte.pdf', file_content)
        >>> url = storage.get_url(path, expiration=3600)
    """
    
    @abstractmethod
    def save(self, path: str, content: BinaryIO, 
             content_type: Optional[str] = None) -> str:
        """
        Sauvegarde un fichier.
        
        PARAMÈTRES:
            path: Chemin de destination
            content: Contenu binaire
            content_type: MIME type
            
        RETOURNE:
            Chemin/identifiant du fichier stocké
        """
        pass
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        """
        Supprime un fichier.
        
        PARAMÈTRES:
            path: Chemin du fichier
            
        RETOURNE:
            True si supprimé
        """
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Vérifie si un fichier existe."""
        pass
    
    @abstractmethod
    def get_url(self, path: str, expiration: Optional[int] = None) -> str:
        """
        Génère une URL d'accès.
        
        PARAMÈTRES:
            path: Chemin du fichier
            expiration: Durée de validité en secondes (None = permanent)
            
        RETOURNE:
            URL accessible
        """
        pass
    
    @abstractmethod
    def get_size(self, path: str) -> int:
        """Retourne la taille du fichier en octets."""
        pass


# ============================================================================
# NOTIFICATION PUSH SERVICE
# ============================================================================

@dataclass
class PushNotification:
    """Notification push à envoyer."""
    title: str
    body: str
    device_tokens: List[str]
    data: Optional[Dict] = None
    priority: str = "normal"  # normal, high


class PushNotificationInterface(ABC):
    """
    Interface pour les notifications push.
    
    IMPLEMENTATIONS:
        - Firebase Cloud Messaging (FCM)
        - Apple Push Notification Service (APNS)
        - OneSignal
    """
    
    @abstractmethod
    def send(self, notification: PushNotification) -> Dict[str, bool]:
        """
        Envoie une notification push.
        
        RETOURNE:
            Statut par device token
        """
        pass
    
    @abstractmethod
    def subscribe_topic(self, device_token: str, topic: str) -> bool:
        """Abonne un device à un topic."""
        pass
    
    @abstractmethod
    def unsubscribe_topic(self, device_token: str, topic: str) -> bool:
        """Désabonne un device d'un topic."""
        pass


# ============================================================================
# CACHE SERVICE
# ============================================================================

class CacheServiceInterface(ABC):
    """
    Interface pour le service de cache.
    
    IMPLEMENTATIONS:
        - Redis
        - Memcached
        - Django Cache
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Stocke une valeur dans le cache.
        
        PARAMÈTRES:
            key: Clé
            value: Valeur à stocker
            ttl: Temps de vie en secondes
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Supprime une clé du cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Vérifie si une clé existe."""
        pass
    
    @abstractmethod
    def flush(self) -> bool:
        """Vide le cache."""
        pass


# ============================================================================
# LOGGER SERVICE
# ============================================================================

class LoggerInterface(ABC):
    """
    Interface pour la journalisation.
    
    Permet de changer d'implémentation (console, fichier, cloud)
    sans modifier le code métier.
    """
    
    @abstractmethod
    def debug(self, message: str, context: Optional[Dict] = None) -> None:
        """Log niveau DEBUG."""
        pass
    
    @abstractmethod
    def info(self, message: str, context: Optional[Dict] = None) -> None:
        """Log niveau INFO."""
        pass
    
    @abstractmethod
    def warning(self, message: str, context: Optional[Dict] = None) -> None:
        """Log niveau WARNING."""
        pass
    
    @abstractmethod
    def error(self, message: str, context: Optional[Dict] = None) -> None:
        """Log niveau ERROR."""
        pass
    
    @abstractmethod
    def critical(self, message: str, context: Optional[Dict] = None) -> None:
        """Log niveau CRITICAL."""
        pass
