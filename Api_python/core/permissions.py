"""
Permissions personnalisées pour le MVC
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission qui permet à l'utilisateur de modifier uniquement ses propres ressources.
    """
    
    def has_object_permission(self, request, view, obj):
        # Lecture toujours autorisée
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier si l'utilisateur est propriétaire
        return hasattr(obj, 'utilisateur') and obj.utilisateur == request.user


class IsAgentOrAdmin(permissions.BasePermission):
    """
    Permission qui vérifie si l'utilisateur est un agent ou un admin.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_agent_or_admin


class IsCitoyen(permissions.BasePermission):
    """
    Permission qui vérifie si l'utilisateur est un citoyen.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == 'citoyen'


class IsAdminOnly(permissions.BasePermission):
    """
    Permission qui vérifie si l'utilisateur est un administrateur.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.role == 'administrateur'


class IsOwnerOrAgentOrAdmin(permissions.BasePermission):
    """
    Permission qui permet au propriétaire, aux agents et aux admins.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Agents et admins peuvent tout faire
        if request.user.is_agent_or_admin:
            return True
        
        # Le propriétaire peut modifier
        return hasattr(obj, 'utilisateur') and obj.utilisateur == request.user


class ReadOnly(permissions.BasePermission):
    """
    Permission qui autorise uniquement la lecture.
    """
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsCreatorOrReadOnly(permissions.BasePermission):
    """
    Permission qui permet au créateur de modifier.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return hasattr(obj, 'created_by') and obj.created_by == request.user
