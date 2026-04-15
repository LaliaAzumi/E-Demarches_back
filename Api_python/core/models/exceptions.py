"""
Exceptions personnalisées pour la gestion des erreurs métier.
"""


class CoreException(Exception):
    """Exception de base pour l'application core."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or 'CORE_ERROR'
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {
            'error': self.code,
            'message': self.message,
            'details': self.details,
        }


class ValidationException(CoreException):
    """Exception pour les erreurs de validation de données."""
    
    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(
            message=message,
            code='VALIDATION_ERROR',
            details={'field': field, **(details or {})}
        )
        self.field = field


class AuthentificationException(CoreException):
    """Exception pour les erreurs d'authentification."""
    
    def __init__(self, message: str = "Authentification échouée", details: dict = None):
        super().__init__(
            message=message,
            code='AUTH_ERROR',
            details=details or {}
        )


class PermissionException(CoreException):
    """Exception pour les erreurs de permissions."""
    
    def __init__(self, message: str = "Permission insuffisante", required_role: str = None):
        super().__init__(
            message=message,
            code='PERMISSION_DENIED',
            details={'required_role': required_role}
        )
        self.required_role = required_role


class DemandeException(CoreException):
    """Exception pour les erreurs liées aux demandes."""
    
    STATUT_INVALIDE = 'STATUT_INVALIDE'
    DEMANDE_INEXISTANTE = 'DEMANDE_INEXISTANTE'
    TRANSITION_INVALIDE = 'TRANSITION_INVALIDE'
    DEMANDEDeja_TRAITEE = 'DEMANDEDeja_TRAITEE'
    
    def __init__(self, message: str, error_code: str = None, demande_id: int = None):
        super().__init__(
            message=message,
            code=error_code or 'DEMANDE_ERROR',
            details={'demande_id': demande_id}
        )
        self.demande_id = demande_id


class DocumentException(CoreException):
    """Exception pour les erreurs liées aux documents."""
    
    FICHIER_TROP_GROS = 'FICHIER_TROP_GROS'
    TYPE_INVALIDE = 'TYPE_INVALIDE'
    FICHIER_CORROMPU = 'FICHIER_CORROMPU'
    DOCUMENT_INEXISTANT = 'DOCUMENT_INEXISTANT'
    
    def __init__(self, message: str, error_code: str = None, fichier_nom: str = None):
        super().__init__(
            message=message,
            code=error_code or 'DOCUMENT_ERROR',
            details={'fichier': fichier_nom}
        )
        self.fichier_nom = fichier_nom


class RDVException(CoreException):
    """Exception pour les erreurs liées aux rendez-vous."""
    
    CRENEAU_INDISPONIBLE = 'CRENEAU_INDISPONIBLE'
    RDVDeja_CONFIRME = 'RDVDeja_CONFIRME'
    RDV_EXPIRE = 'RDV_EXPIRE'
    PROPOSITION_INVALIDE = 'PROPOSITION_INVALIDE'
    
    def __init__(self, message: str, error_code: str = None, date: str = None, heure: str = None):
        super().__init__(
            message=message,
            code=error_code or 'RDV_ERROR',
            details={'date': date, 'heure': heure}
        )
        self.date = date
        self.heure = heure


class NotificationException(CoreException):
    """Exception pour les erreurs de notification."""
    
    ENVOI_ECHOUE = 'ENVOI_ECHOUE'
    UTILISATEUR_INJOIGNABLE = 'UTILISATEUR_INJOIGNABLE'
    
    def __init__(self, message: str, error_code: str = None, utilisateur_id: int = None):
        super().__init__(
            message=message,
            code=error_code or 'NOTIFICATION_ERROR',
            details={'utilisateur_id': utilisateur_id}
        )


class ProfilException(CoreException):
    """Exception pour les erreurs de profil utilisateur."""
    
    PROFIL_INCOMPLET = 'PROFIL_INCOMPLET'
    CIN_INVALIDE = 'CIN_INVALIDE'
    EMAILDeja_UTILISE = 'EMAILDeja_UTILISE'
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(
            message=message,
            code=error_code or 'PROFIL_ERROR'
        )
