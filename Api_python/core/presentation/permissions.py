"""
================================================================================
MODULE: permissions.py
COUCHE: Presentation
RÔLE: Permissions personnalisées pour l'API REST

ARCHITECTURE:
    Les permissions contrôlent l'accès aux endpoints API.
    Elles s'intègrent avec Django REST Framework.

    IsCitoyen: Accès réservé aux citoyens
    IsAgent: Accès réservé aux agents
    IsAdministrateur: Accès réservé aux admins
    IsOwnerOrAdmin: Accès au propriétaire ou admin
    CanAccessDemande: Permission spécifique aux demandes

PATTERN: Permission Classes (Django REST Framework)
AGILE: Permissions = Access Control pour User Stories
================================================================================
"""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View

from ..domain.value_objects import Role
from ..domain.exceptions import PermissionDeniedException


# ============================================================================
# PERMISSIONS BASÉES SUR LES RÔLES
# ============================================================================

class IsCitoyen(permissions.BasePermission):
    """
    Permission: Accès réservé aux citoyens.
    
    UTILISATION:
        @permission_classes([IsCitoyen])
        def soumettre_demande(request):
            ...
    
    MESSAGE: "Accès réservé aux citoyens"
    """
    
    message = "Accès réservé aux citoyens"
    
    def has_permission(self, request: Request, view: View) -> bool:
        """
        Vérifie que l'utilisateur est authentifié et est un citoyen.
        
        PARAMÈTRES:
            request: Requête HTTP
            view: Vue appelée
            
        RETOURNE:
            True si citoyen, False sinon
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Vérifier le rôle
        return (
            hasattr(request.user, 'role') and 
            request.user.role == Role.CITOYEN.value
        )


class IsAgent(permissions.BasePermission):
    """
    Permission: Accès réservé aux agents administratifs.
    
    UTILISATION:
        @permission_classes([IsAgent])
        def traiter_demande(request):
            ...
    
    MESSAGE: "Accès réservé aux agents administratifs"
    """
    
    message = "Accès réservé aux agents administratifs"
    
    def has_permission(self, request: Request, view: View) -> bool:
        """Vérifie que l'utilisateur est un agent."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            hasattr(request.user, 'role') and 
            request.user.role == Role.AGENT.value
        )


class IsAdministrateur(permissions.BasePermission):
    """
    Permission: Accès réservé aux administrateurs.
    
    UTILISATION:
        @permission_classes([IsAdministrateur])
        def gerer_utilisateurs(request):
            ...
    
    MESSAGE: "Accès réservé aux administrateurs"
    """
    
    message = "Accès réservé aux administrateurs"
    
    def has_permission(self, request: Request, view: View) -> bool:
        """Vérifie que l'utilisateur est un administrateur."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return (
            hasattr(request.user, 'role') and 
            request.user.role == Role.ADMINISTRATEUR.value
        )


class IsAdminOrAgent(permissions.BasePermission):
    """
    Permission: Accès réservé aux agents et administrateurs.
    
    UTILISATION:
        @permission_classes([IsAdminOrAgent])
        def voir_toutes_demandes(request):
            ...
    """
    
    message = "Accès réservé aux agents et administrateurs"
    
    def has_permission(self, request: Request, view: View) -> bool:
        """Vérifie agent ou admin."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        role = getattr(request.user, 'role', None)
        return role in [Role.AGENT.value, Role.ADMINISTRATEUR.value]


# ============================================================================
# PERMISSIONS BASÉES SUR LA PROPRIÉTÉ
# ============================================================================

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission: Accès au propriétaire de la ressource ou aux admins.
    
    UTILISATION:
        @permission_classes([IsOwnerOrAdmin])
        def modifier_profil(request, pk):
            ...
    
    LOGIQUE:
        - Un utilisateur peut voir/modifier ses propres données
        - Un admin peut voir/modifier toutes les données
    
    EXEMPLE:
        >>> user = request.user
        >>> obj = get_object()
        >>> permission = (user.id == obj.user_id) or user.is_admin
    """
    
    message = "Vous n'avez pas accès à cette ressource"
    
    def has_object_permission(
        self,
        request: Request,
        view: View,
        obj
    ) -> bool:
        """
        Vérifie la permission au niveau de l'objet.
        
        PARAMÈTRES:
            request: Requête HTTP
            view: Vue appelée
            obj: Objet concerné (doit avoir user_id ou citoyen_id)
            
        RETOURNE:
            True si propriétaire ou admin
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin a toujours accès
        if self._is_admin(user):
            return True
        
        # Vérifier propriété
        owner_id = self._get_owner_id(obj)
        return owner_id is not None and user.id == owner_id
    
    def _is_admin(self, user) -> bool:
        """Vérifie si l'utilisateur est admin."""
        return (
            getattr(user, 'role', None) == Role.ADMINISTRATEUR.value or
            getattr(user, 'is_superuser', False)
        )
    
    def _get_owner_id(self, obj) -> int:
        """
        Récupère l'ID du propriétaire de l'objet.
        
        Cherche les attributs: user_id, citoyen_id, owner_id, created_by_id
        """
        for attr in ['user_id', 'citoyen_id', 'owner_id', 'created_by_id', 'utilisateur_id']:
            if hasattr(obj, attr):
                return getattr(obj, attr)
        return None


class IsOwnerOrAssignedAgent(permissions.BasePermission):
    """
    Permission: Accès au propriétaire ou à l'agent assigné.
    
    SPÉCIFIQUE AUX: Demandes administratives
    
    LOGIQUE:
        - Le citoyen créateur peut voir sa demande
        - L'agent assigné peut voir la demande
        - Un admin peut tout voir
    """
    
    message = "Vous n'avez pas accès à cette demande"
    
    def has_object_permission(
        self,
        request: Request,
        view: View,
        obj
    ) -> bool:
        """Vérifie l'accès à la demande."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin a toujours accès
        if self._is_admin(user):
            return True
        
        # Citoyen propriétaire
        if self._is_citoyen(user) and hasattr(obj, 'citoyen_id'):
            if user.id == obj.citoyen_id:
                return True
        
        # Agent assigné
        if self._is_agent(user) and hasattr(obj, 'agent_id'):
            if user.id == obj.agent_id:
                return True
        
        return False
    
    def _is_admin(self, user) -> bool:
        return getattr(user, 'role', None) == Role.ADMINISTRATEUR.value
    
    def _is_citoyen(self, user) -> bool:
        return getattr(user, 'role', None) == Role.CITOYEN.value
    
    def _is_agent(self, user) -> bool:
        return getattr(user, 'role', None) == Role.AGENT.value


# ============================================================================
# PERMISSIONS SPÉCIFIQUES
# ============================================================================

class CanAccessDemande(permissions.BasePermission):
    """
    Permission complète pour les demandes.
    
    VÉRIFIE:
        1. Utilisateur authentifié
        2. Accès autorisé selon rôle et relation
    
    UTILISATION:
        class DemandeViewSet(viewsets.ModelViewSet):
            permission_classes = [CanAccessDemande]
    """
    
    message = "Accès non autorisé à cette demande"
    
    def has_permission(self, request: Request, view: View) -> bool:
        """Vérifie l'authentification."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(
        self,
        request: Request,
        view: View,
        obj
    ) -> bool:
        """
        Vérifie l'accès à une demande spécifique.
        
        RÈGLES:
            - Citoyen: peut voir ses propres demandes
            - Agent: peut voir les demandes qui lui sont assignées
            - Admin: peut tout voir
        """
        user = request.user
        
        # Admin
        if getattr(user, 'role', None) == Role.ADMINISTRATEUR.value:
            return True
        
        # Vérifier rôles et accès
        role = getattr(user, 'role', None)
        
        # Citoyen - propriétaire
        if role == Role.CITOYEN.value:
            citoyen_id = getattr(obj, 'citoyen_id', None)
            return citoyen_id is not None and user.id == citoyen_id
        
        # Agent - assigné
        if role == Role.AGENT.value:
            agent_id = getattr(obj, 'agent_id', None)
            return agent_id is not None and user.id == agent_id
        
        return False


class CanModifyDemande(permissions.BasePermission):
    """
    Permission de modification pour les demandes.
    
    RÈGLES:
        - Citoyen: peut modifier uniquement ses brouillons
        - Agent: peut modifier les demandes qui lui sont assignées
        - Admin: peut tout modifier
    """
    
    message = "Vous ne pouvez pas modifier cette demande"
    
    def has_object_permission(
        self,
        request: Request,
        view: View,
        obj
    ) -> bool:
        """Vérifie la permission de modification."""
        user = request.user
        
        # Admin
        if getattr(user, 'role', None) == Role.ADMINISTRATEUR.value:
            return True
        
        role = getattr(user, 'role', None)
        
        # Citoyen - brouillon uniquement
        if role == Role.CITOYEN.value:
            if user.id != getattr(obj, 'citoyen_id', None):
                return False
            # Vérifier statut brouillon
            return getattr(obj, 'status', None) == 'brouillon'
        
        # Agent - demandes assignées
        if role == Role.AGENT.value:
            return user.id == getattr(obj, 'agent_id', None)
        
        return False


class CanCreateDemande(permissions.BasePermission):
    """
    Permission de création de demandes.
    
    RÈGLE: Seuls les citoyens peuvent créer des demandes.
    """
    
    message = "Seuls les citoyens peuvent créer des demandes"
    
    def has_permission(self, request: Request, view: View) -> bool:
        """Vérifie que l'utilisateur est un citoyen."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return getattr(request.user, 'role', None) == Role.CITOYEN.value


# ============================================================================
# PERMISSIONS COMPOSÉES
# ============================================================================

class ReadOnly(permissions.BasePermission):
    """
    Permission: Accès lecture seule.
    
    UTILISATION:
        @permission_classes([IsAuthenticated & ReadOnly])
    """
    
    def has_permission(self, request: Request, view: View) -> bool:
        """Autorise uniquement les méthodes de lecture."""
        return request.method in permissions.SAFE_METHODS


class IsAuthenticatedAndActive(permissions.BasePermission):
    """
    Permission: Utilisateur authentifié ET actif.
    
    VÉRIFIE:
        - is_authenticated = True
        - is_active = True
    """
    
    message = "Votre compte est désactivé"
    
    def has_permission(self, request: Request, view: View) -> bool:
        """Vérifie authentification et compte actif."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return getattr(request.user, 'is_active', True)


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_permission_message(permission_class) -> str:
    """
    Récupère le message d'une permission.
    
    PARAMÈTRES:
        permission_class: Classe de permission
        
    RETOURNE:
        Message explicatif
    """
    return getattr(permission_class, 'message', "Permission refusée")


def check_permission(user, required_role: Role) -> bool:
    """
    Vérifie si l'utilisateur a le rôle requis.
    
    PARAMÈTRES:
        user: Utilisateur à vérifier
        required_role: Rôle requis
        
    RETOURNE:
        True si l'utilisateur a le rôle requis
        
    LÈVE:
        PermissionDeniedException: Si rôle insuffisant
    """
    if not user or not user.is_authenticated:
        raise PermissionDeniedException("Authentification requise")
    
    user_role = getattr(user, 'role', None)
    
    if user_role != required_role.value:
        # Vérifier si admin (qui a tous les droits)
        if user_role != Role.ADMINISTRATEUR.value:
            raise PermissionDeniedException(
                message=f"Rôle '{required_role.label}' requis",
                required_permission=required_role.value,
                current_user_role=user_role
            )
    
    return True


def require_citoyen(user):
    """Vérifie que l'utilisateur est un citoyen."""
    return check_permission(user, Role.CITOYEN)


def require_agent(user):
    """Vérifie que l'utilisateur est un agent."""
    return check_permission(user, Role.AGENT)


def require_admin(user):
    """Vérifie que l'utilisateur est un admin."""
    return check_permission(user, Role.ADMINISTRATEUR)
