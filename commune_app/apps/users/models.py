from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import date


class UtilisateurManager(BaseUserManager):
    def create_user(self, email, nom, mot_de_passe=None, role='citoyen', **extra_fields):
        if not email:
            raise ValueError('L\'email est obligatoire')
        email = self.normalize_email(email)
        user = self.model(email=email, nom=nom, role=role, **extra_fields)
        user.set_password(mot_de_passe)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nom, mot_de_passe=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nom, mot_de_passe, role='agent', **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('citoyen', 'Citoyen'),
        ('agent', 'Agent'),
    ]

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # is_first_login removed - guide/onboarding removed
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UtilisateurManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom']

    class Meta:
        db_table = 'utilisateurs'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.nom} ({self.get_role_display()})"


class Citoyen(models.Model):
    id = models.AutoField(primary_key=True)
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'citoyen'},
        db_column='utilisateur_id'
    )
    prenom = models.CharField(max_length=100, null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    cin = models.CharField(max_length=20, unique=True, null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'citoyens'
        verbose_name = 'Citoyen'
        verbose_name_plural = 'Citoyens'
        indexes = [
            models.Index(fields=['utilisateur']),
            models.Index(fields=['cin']),
        ]

    def __str__(self):
        return f"Citoyen: {self.utilisateur.nom}"


class Agent(models.Model):
    id = models.AutoField(primary_key=True)
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'agent'},
        db_column='utilisateur_id'
    )
    matricule = models.CharField(max_length=50, null=True, blank=True)
    service = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'agents'
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
        indexes = [
            models.Index(fields=['utilisateur']),
            models.Index(fields=['matricule']),
        ]

    def __str__(self):
        return f"Agent: {self.utilisateur.nom}"
