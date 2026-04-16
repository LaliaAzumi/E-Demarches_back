"""
================================================================================
MODULE: exceptions.py
COUCHE: Domain
RÔLE: Définition des exceptions métier personnalisées

ARCHITECTURE:
    - DomainException (Classe base abstraite)
        ├── ValidationException (Erreurs de validation données)
        ├── NotFoundException (Ressource non trouvée)
        ├── PermissionDeniedException (Accès non autorisé)
        ├── BusinessRuleException (Violation règle métier)
        └── AuthenticationException (Erreur authentification)

AGILE: Ces exceptions traduisent les erreurs métier en langage compréhensible
================================================================================
"""

from typing import Optional, Dict, Any
from enum import Enum


class ExceptionCode(Enum):
    """
    Énumération des codes d'erreur métier.
    
    Permet une identification standardisée des erreurs pour le frontend
    et la gestion des erreurs côté API.
    """
    # Erreurs générales (1000-1099)
    UNKNOWN_ERROR = "ERR_1000"
    VALIDATION_ERROR = "ERR_1001"
    NOT_FOUND = "ERR_1002"
    PERMISSION_DENIED = "ERR_1003"
    
    # Erreurs authentification (1100-1199)
    AUTH_INVALID_CREDENTIALS = "ERR_1100"
    AUTH_TOKEN_EXPIRED = "ERR_1101"
    AUTH_ACCOUNT_DISABLED = "ERR_1102"
    AUTH_EMAIL_EXISTS = "ERR_1103"
    
    # Erreurs métier demandes (1200-1299)
    DEMANDE_INVALID_STATUS = "ERR_1200"
    DEMANDE_ALREADY_ASSIGNED = "ERR_1201"
    DEMANDE_DEADLINE_EXCEEDED = "ERR_1202"
    
    # Erreurs RDV (1300-1399)
    RDV_CONFLICT = "ERR_1300"
    RDV_EXPIRED = "ERR_1301"


class DomainException(Exception):
    """
    Classe base abstraite pour toutes les exceptions métier.
    
    Cette classe sert de fondation pour toutes les erreurs spécifiques
    au domaine de l'application administrative.
    
    ATTRIBUTS:
        message (str): Description lisible de l'erreur
        code (ExceptionCode): Code standardisé de l'erreur
        field (str): Champ concerné (pour les erreurs de validation)
        details (dict): Informations supplémentaires contextuelles
    
    EXEMPLE:
        >>> raise DomainException(
        ...     "Opération non autorisée",
        ...     code=ExceptionCode.PERMISSION_DENIED,
        ...     details={'user_id': 123, 'required_role': 'admin'}
        ... )
    """
    
    def __init__(
        self,
        message: str,
        code: ExceptionCode = ExceptionCode.UNKNOWN_ERROR,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialise une exception de domaine.
        
        PARAMÈTRES:
            message: Description explicite de l'erreur
            code: Code d'erreur standardisé
            field: Nom du champ en erreur (si applicable)
            details: Dictionnaire de données contextuelles
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.field = field
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'exception en dictionnaire pour l'API.
        
        RETOURNE:
            dict: Représentation structurée de l'erreur
        """
        return {
            'success': False,
            'error': {
                'code': self.code.value,
                'message': self.message,
                'field': self.field,
                'details': self.details
            }
        }
    
    def __str__(self) -> str:
        """Représentation string de l'exception."""
        base = f"[{self.code.value}] {self.message}"
        if self.field:
            base += f" (field: {self.field})"
        return base
    
    def __repr__(self) -> str:
        """Représentation détaillée pour le debugging."""
        return (
            f"<{self.__class__.__name__}: "
            f"code={self.code.value}, "
            f"message='{self.message}', "
            f"field={self.field}>"
        )


class ValidationException(DomainException):
    """
    Exception levée lors d'une erreur de validation de données.
    
    UTILISATION:
        - Validation des formulaires
        - Contrôle de cohérence des données
        - Vérification des formats (email, téléphone, etc.)
    
    EXEMPLE:
        >>> if not email.contains('@'):
        ...     raise ValidationException(
        ...         "Format d'email invalide",
        ...         code=ExceptionCode.VALIDATION_ERROR,
        ...         field='email'
        ...     )
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialise une exception de validation."""
        super().__init__(
            message=message,
            code=ExceptionCode.VALIDATION_ERROR,
            field=field,
            details=details
        )


class NotFoundException(DomainException):
    """
    Exception levée lorsqu'une ressource n'est pas trouvée.
    
    UTILISATION:
        - Recherche d'utilisateur inexistant
        - Demande administrative non trouvée
        - Document manquant
    
    EXEMPLE:
        >>> try:
        ...     user = User.objects.get(pk=user_id)
        ... except User.DoesNotExist:
        ...     raise NotFoundException(
        ...         f"Utilisateur avec ID {user_id} non trouvé",
        ...         details={'resource': 'user', 'id': user_id}
        ...     )
    """
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None
    ):
        """
        Initialise une exception de ressource non trouvée.
        
        PARAMÈTRES:
            message: Description de l'erreur
            resource_type: Type de la ressource (ex: 'user', 'demande')
            resource_id: Identifiant de la ressource recherchée
        """
        details = {}
        if resource_type:
            details['resource'] = resource_type
        if resource_id:
            details['id'] = resource_id
            
        super().__init__(
            message=message,
            code=ExceptionCode.NOT_FOUND,
            details=details
        )


class PermissionDeniedException(DomainException):
    """
    Exception levée lors d'un accès non autorisé.
    
    UTILISATION:
        - Accès à une ressource d'un autre utilisateur
        - Action réservée à un rôle supérieur
        - Tentative de modification sans droits
    
    EXEMPLE:
        >>> if not user.is_admin:
        ...     raise PermissionDeniedException(
        ...         "Accès réservé aux administrateurs",
        ...         details={'required_role': 'admin', 'user_role': user.role}
        ...     )
    """
    
    def __init__(
        self,
        message: str,
        required_permission: Optional[str] = None,
        current_user_role: Optional[str] = None
    ):
        """Initialise une exception de permission."""
        details = {}
        if required_permission:
            details['required_permission'] = required_permission
        if current_user_role:
            details['current_role'] = current_user_role
            
        super().__init__(
            message=message,
            code=ExceptionCode.PERMISSION_DENIED,
            details=details
        )


class BusinessRuleException(DomainException):
    """
    Exception levée lors d'une violation de règle métier.
    
    UTILISATION:
        - Transition de statut interdite
        - Contraintes temporelles
        - Limites de quota ou de volume
    
    EXEMPLE:
        >>> if demande.statut != 'soumise':
        ...     raise BusinessRuleException(
        ...         "Impossible d'assigner une demande non soumise",
        ...         code=ExceptionCode.DEMANDE_INVALID_STATUS,
        ...         details={'current_status': demande.statut}
        ...     )
    """
    
    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        code: ExceptionCode = ExceptionCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialise une exception de règle métier."""
        all_details = details or {}
        if rule_name:
            all_details['rule'] = rule_name
            
        super().__init__(
            message=message,
            code=code,
            details=all_details
        )


class AuthenticationException(DomainException):
    """
    Exception levée lors d'une erreur d'authentification.
    
    UTILISATION:
        - Identifiants invalides
        - Token expiré ou invalide
        - Compte désactivé
    
    EXEMPLE:
        >>> if not user.check_password(password):
        ...     raise AuthenticationException(
        ...         "Mot de passe incorrect",
        ...         code=ExceptionCode.AUTH_INVALID_CREDENTIALS
        ...     )
    """
    
    def __init__(
        self,
        message: str,
        code: ExceptionCode = ExceptionCode.AUTH_INVALID_CREDENTIALS,
        auth_method: Optional[str] = None
    ):
        """Initialise une exception d'authentification."""
        details = {}
        if auth_method:
            details['method'] = auth_method
            
        super().__init__(
            message=message,
            code=code,
            details=details
        )


# ============================================================================
# EXCEPTIONS SPÉCIFIQUES AU MÉTIER
# ============================================================================

class DemandeException(BusinessRuleException):
    """Exception spécifique aux demandes administratives."""
    
    def __init__(self, message: str, code: ExceptionCode, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            rule_name='demande_rule',
            code=code,
            details=details
        )


class RDVException(BusinessRuleException):
    """Exception spécifique aux rendez-vous."""
    
    def __init__(self, message: str, code: ExceptionCode, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            rule_name='rdv_rule',
            code=code,
            details=details
        )


class DocumentException(BusinessRuleException):
    """Exception spécifique aux documents."""
    
    def __init__(self, message: str, code: ExceptionCode, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            rule_name='document_rule',
            code=code,
            details=details
        )


class NotificationException(BusinessRuleException):
    """Exception spécifique aux notifications."""
    
    def __init__(self, message: str, code: ExceptionCode, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            rule_name='notification_rule',
            code=code,
            details=details
        )
