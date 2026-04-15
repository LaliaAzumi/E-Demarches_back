"""
Serializers pour les utilisateurs
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from dj_rest_auth.registration.serializers import RegisterSerializer

from ..models import Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    """
    Serializer de base pour Utilisateur.
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    nom_complet = serializers.CharField(read_only=True)
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'email', 'nom', 'prenom', 'telephone',
            'role', 'role_display', 'nom_complet',
            'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class UtilisateurCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour créer un utilisateur avec mot de passe.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = Utilisateur
        fields = [
            'email', 'nom', 'prenom', 'telephone',
            'role', 'password', 'password_confirm'
        ]
    
    def validate(self, data):
        """Valide que les mots de passe correspondent."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        return data
    
    def create(self, validated_data):
        """Crée l'utilisateur avec hash du mot de passe."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        utilisateur = Utilisateur.objects.create(**validated_data)
        utilisateur.set_password(password)
        utilisateur.save()
        
        return utilisateur


class LoginSerializer(serializers.Serializer):
    """
    Serializer pour l'authentification.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        """Valide les credentials."""
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Email ou mot de passe incorrect")
        if not user.is_active:
            raise serializers.ValidationError("Ce compte est désactivé")
        return user


class CustomRegisterSerializer(RegisterSerializer):
    """
    Serializer personnalisé pour dj-rest-auth avec création de profil citoyen.
    """
    nom = serializers.CharField(max_length=100, required=True)
    prenom = serializers.CharField(max_length=100, required=True)
    telephone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate(self, data):
        # Appeler la validation parent (email, password1, password2)
        data = super().validate(data)
        return data

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['nom'] = self.validated_data.get('nom', '')
        data['prenom'] = self.validated_data.get('prenom', '')
        data['telephone'] = self.validated_data.get('telephone', '')
        return data

    def custom_signup(self, request, user):
        """Crée le profil citoyen après l'inscription."""
        from ..models import Citoyen
        user.nom = self.validated_data.get('nom', '')
        user.prenom = self.validated_data.get('prenom', '')
        user.telephone = self.validated_data.get('telephone', '')
        user.role = 'citoyen'
        user.save()
        Citoyen.objects.create(utilisateur=user)


class GoogleAuthSerializer(serializers.Serializer):
    """
    Serializer pour l'authentification Google OAuth.
    """
    access_token = serializers.CharField(required=True, help_text="Token d'accès Google")
    id_token = serializers.CharField(required=False, allow_blank=True, help_text="ID Token Google (optional)")
    
    def validate_access_token(self, value):
        """Valide le format du token."""
        if not value or len(value) < 20:
            raise serializers.ValidationError("Token d'accès invalide")
        return value
