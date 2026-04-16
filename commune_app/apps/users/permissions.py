from rest_framework import permissions


class IsAgent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'agent'


class IsCitoyen(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'citoyen'


class IsOwnerOrAgent(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'agent':
            return True
        return obj.id == request.user.id
