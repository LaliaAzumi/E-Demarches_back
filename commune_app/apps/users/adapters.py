from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model
from .models import Utilisateur, Citoyen


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapter personnalisé pour lier les comptes Google OAuth
    avec notre modèle Utilisateur personnalisé.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Appelé avant le login social.
        Vérifie si un utilisateur existe déjà avec cet email.
        """
        email = sociallogin.account.extra_data.get('email')
        if not email:
            return

        # Chercher un utilisateur existant avec cet email
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            # Lier le compte social à l'utilisateur existant
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """
        Crée un nouvel utilisateur à partir des données Google OAuth.
        """
        user = super().save_user(request, sociallogin, form)

        # Extraire les données de Google
        extra_data = sociallogin.account.extra_data
        email = extra_data.get('email', '')
        first_name = extra_data.get('given_name', '')
        last_name = extra_data.get('family_name', '')

        # Mettre à jour les champs utilisateur
        user.nom = f"{first_name} {last_name}".strip() or email.split('@')[0]
        user.role = 'citoyen'  # Par défaut, les utilisateurs OAuth sont des citoyens
        user.save()

        # Créer automatiquement un profil Citoyen
        Citoyen.objects.get_or_create(
            utilisateur=user,
            defaults={'cin': None, 'adresse': None}
        )

        return user

    def is_open_for_signup(self, request, sociallogin):
        """
        Permet l'inscription via OAuth (Google).
        """
        return True
