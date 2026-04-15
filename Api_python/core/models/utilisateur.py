"""
Modèle Utilisateur et son Manager personnalisé.
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Count, Q

from .mixins import TimestampMixin
from .exceptions import ValidationException, AuthentificationException, ProfilException


class UtilisateurManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle Utilisateur.
    
    Fournit des méthodes de création et de recherche spécialisées.
    """
    
    def create_user(self, email: str, nom: str, prenom: str, telephone: str, 
                    password: str = None, role: str = 'citoyen') -> 'Utilisateur':
        """
        Crée et sauvegarde un utilisateur avec email et mot de passe.
        
        Args:
            email: Email unique de l'utilisateur
            nom: Nom de famille
            prenom: Prénom
            telephone: Numéro de téléphone
            password: Mot de passe (optionnel)
            role: Rôle de l'utilisateur
            
        Returns:
            Utilisateur: L'instance créée
            
        Raises:
            ValidationException: Si les données sont invalides
        """
        if not email:
            raise ValidationException("L'email est obligatoire", field='email')
        if not nom or not prenom:
            raise ValidationException("Le nom et prénom sont obligatoires", field='nom')
        
        # Vérifier l'unicité de l'email
        email = self.normalize_email(email)
        if self.filter(email__iexact=email).exists():
            raise ProfilException("Cet email est déjà utilisé", ProfilException.EMAILDeja_UTILISE)
        
        try:
            user = self.model(
                email=email, 
                nom=nom.strip().upper(), 
                prenom=prenom.strip().title(), 
                telephone=telephone, 
                role=role
            )
            user.set_password(password)
            user.save(using=self._db)
            return user
        except Exception as e:
            raise ValidationException(f"Erreur lors de la création: {str(e)}")

    def create_superuser(self, email: str, nom: str, prenom: str, 
                         telephone: str, password: str = None) -> 'Utilisateur':
        """Crée un superutilisateur (administrateur)."""
        user = self.create_user(email, nom, prenom, telephone, password, 
                                role=Utilisateur.Role.ADMINISTRATEUR)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    
    def agents_actifs(self):
        """Retourne uniquement les agents actifs."""
        return self.filter(role=Utilisateur.Role.AGENT, is_active=True)
    
    def citoyens_inscrits_ce_mois(self):
        """Retourne les citoyens inscrits ce mois."""
        now = timezone.now()
        return self.filter(
            role=Utilisateur.Role.CITOYEN, 
            created_at__month=now.month,
            created_at__year=now.year
        )
    
    def rechercher(self, query: str):
        """Recherche un utilisateur par nom, prénom ou email."""
        return self.filter(
            Q(nom__icontains=query) | 
            Q(prenom__icontains=query) | 
            Q(email__icontains=query)
        )


class Utilisateur(AbstractBaseUser, PermissionsMixin, TimestampMixin):
    """
    Modèle utilisateur personnalisé avec authentification par email.
    
    Attributs:
        email: Email unique (identifiant)
        nom: Nom de famille
        prenom: Prénom
        telephone: Numéro de contact
        role: Rôle (citoyen, agent, administrateur)
        is_active: Compte actif ou non
        is_staff: Accès admin Django
    """
    
    class Role(models.TextChoices):
        CITOYEN = 'citoyen', 'Citoyen'
        AGENT = 'agent', 'Agent administratif'
        ADMINISTRATEUR = 'administrateur', 'Administrateur'

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    email = models.EmailField(max_length=100, unique=True, verbose_name="Email")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    role = models.CharField(max_length=20, choices=Role.choices, verbose_name="Rôle")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_staff = models.BooleanField(default=False, verbose_name="Staff")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="Dernière connexion")
    
    # Social Authentication Fields
    auth_provider = models.CharField(max_length=20, blank=True, null=True, verbose_name="Provider OAuth")
    social_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID Social")
    avatar_url = models.URLField(blank=True, null=True, verbose_name="URL Avatar")

    objects = UtilisateurManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom', 'telephone']

    class Meta:
        db_table = 'utilisateurs'
        ordering = ['-created_at']
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self) -> str:
        return f"{self.prenom} {self.nom} ({self.get_role_display()})"
    
    def __repr__(self) -> str:
        return f"<Utilisateur: {self.email} - {self.role}>"
    
    # ========== Propriétés ==========
    
    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet formaté."""
        return f"{self.prenom} {self.nom}"
    
    @property
    def is_citoyen(self) -> bool:
        """Vérifie si l'utilisateur est un citoyen."""
        return self.role == self.Role.CITOYEN
    
    @property
    def is_agent(self) -> bool:
        """Vérifie si l'utilisateur est un agent."""
        return self.role == self.Role.AGENT
    
    @property
    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur est un administrateur."""
        return self.role == self.Role.ADMINISTRATEUR
    
    # ========== Méthodes de validation ==========
    
    def clean(self):
        """Validation personnalisée avant sauvegarde."""
        super().clean()
        if self.email:
            self.email = self.email.lower().strip()
        if self.telephone:
            self.telephone = self.telephone.strip()
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    # ========== Méthodes métier ==========
    
    def get_profile(self):
        """Retourne le profil associé selon le rôle."""
        if self.is_citoyen and hasattr(self, 'citoyen_profile'):
            return self.citoyen_profile
        elif self.is_agent and hasattr(self, 'agent_profile'):
            return self.agent_profile
        elif self.is_admin and hasattr(self, 'admin_profile'):
            return self.admin_profile
        return None
    
    def marquer_notifications_lues(self):
        """Marque toutes les notifications non lues comme lues."""
        self.notifications.filter(lu=False).update(lu=True, date_lecture=timezone.now())
    
    def nombre_notifications_non_lues(self) -> int:
        """Compte les notifications non lues."""
        return self.notifications.filter(lu=False).count()
    
    def notifications_recentes(self, limite: int = 10):
        """Retourne les notifications récentes."""
        return self.notifications.all()[:limite]
    
    def verifier_permission(self, required_role: str):
        """Vérifie si l'utilisateur a la permission requise."""
        from .exceptions import PermissionException
        if self.role != required_role and not self.is_superuser:
            raise PermissionException(
                f"Accès refusé. Rôle requis: {required_role}",
                required_role=required_role
            )
    
    def desactiver(self):
        """Désactive le compte utilisateur."""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def reactiver(self):
        """Réactive le compte utilisateur."""
        self.is_active = True
        self.save(update_fields=['is_active'])
