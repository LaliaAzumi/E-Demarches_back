"""
================================================================================
FICHIER: models.py
APPLICATION: core
RÔLE: Modèles Django ORM - Mapping Domain Entities

ARCHITECTURE:
    Ce fichier mappe les entités du Domain Layer vers les modèles Django ORM.
    Il fait le pont entre la logique métier pure et la persistance.

    ORGANISATION:
        1. Utilisateur (Custom User Model)
        2. Profils (Citoyen, Agent, Administrateur)
        3. Services et Demandes
        4. Documents et Traitements
        5. Rendez-vous
        6. Notifications
        7. FAQ

    HÉRITAGE:
        - Utilisateur hérite de AbstractBaseUser
        - Les autres modèles héritent de models.Model

    MIXINS DJANGO:
        - TimeStampedModel: created_at, updated_at

AGILE: Models = Domain Entities Persistence
================================================================================
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError

# ============================================================================
# MANAGERS PERSONNALISÉS
# ============================================================================

class UtilisateurManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle Utilisateur.
    
    RESPONSABILITÉS:
        - Création d'utilisateurs
        - Création de superutilisateurs
        - Requêtes spécialisées
    
    MÉTHODES:
        create_user: Crée un utilisateur standard
        create_superuser: Crée un administrateur
    """
    
    def create_user(self, email, nom, prenom, telephone='', password=None, role='citoyen'):
        """
        Crée et sauvegarde un utilisateur.
        
        PARAMÈTRES:
            email: Email unique (obligatoire)
            nom: Nom de famille (obligatoire)
            prenom: Prénom (obligatoire)
            telephone: Numéro de téléphone
            password: Mot de passe (optionnel)
            role: Rôle de l'utilisateur
            
        RETOURNE:
            Instance Utilisateur créée
            
        LÈVE:
            ValueError: Si email, nom ou prenom manquant
        """
        if not email:
            raise ValueError("L'email est obligatoire")
        if not nom:
            raise ValueError("Le nom est obligatoire")
        if not prenom:
            raise ValueError("Le prénom est obligatoire")
        
        # Normaliser l'email
        email = self.normalize_email(email)
        
        # Créer l'utilisateur
        user = self.model(
            email=email,
            nom=nom.strip().upper(),
            prenom=prenom.strip().title(),
            telephone=telephone,
            role=role,
        )
        
        # Définir le mot de passe
        if password:
            user.set_password(password)
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, nom, prenom, telephone='', password=None):
        """
        Crée un superutilisateur (administrateur).
        
        PARAMÈTRES:
            Mêmes que create_user
            
        RETOURNE:
            Instance Utilisateur avec droits admin
        """
        user = self.create_user(
            email=email,
            nom=nom,
            prenom=prenom,
            telephone=telephone,
            password=password,
            role='administrateur'
        )
        
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    
    def agents_actifs(self):
        """Retourne les agents actifs."""
        return self.filter(role='agent', is_active=True)
    
    def citoyens_inscrits_mois(self):
        """Retourne les citoyens inscrits ce mois."""
        from datetime import datetime
        now = datetime.now()
        return self.filter(
            role='citoyen',
            created_at__month=now.month,
            created_at__year=now.year
        )


# ============================================================================
# MODÈLE UTILISATEUR
# ============================================================================

class Utilisateur(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur personnalisé avec authentification par email.
    
    CHAMPS:
        - Identification: id, email
        - Authentification: password, last_login
        - Profil: nom, prenom, telephone, role
        - Statut: is_active, is_staff, is_superuser
        - OAuth: auth_provider, social_id, avatar_url
        - Timestamps: created_at, updated_at
    
    CONTRAINTES:
        - Email unique
        - Role dans ['citoyen', 'agent', 'administrateur']
    
    EXEMPLE:
        >>> user = Utilisateur.objects.create_user(
        ...     email='test@example.com',
        ...     nom='DIOP',
        ...     prenom='Amadou'
        ... )
    """
    
    # -------------------------------------------------------------------------
    # CHOIX PRÉDÉFINIS
    # -------------------------------------------------------------------------
    
    ROLE_CHOICES = [
        ('citoyen', 'Citoyen'),
        ('agent', 'Agent administratif'),
        ('administrateur', 'Administrateur'),
    ]
    
    AUTH_PROVIDER_CHOICES = [
        ('', 'Standard'),
        ('google', 'Google'),
        ('facebook', 'Facebook'),
    ]
    
    # -------------------------------------------------------------------------
    # CHAMPS D'IDENTIFICATION
    # -------------------------------------------------------------------------
    
    id = models.AutoField(
        primary_key=True,
        verbose_name="ID"
    )
    
    email = models.EmailField(
        max_length=100,
        unique=True,
        verbose_name="Email",
        validators=[EmailValidator()],
        error_messages={
            'unique': "Cet email est déjà utilisé."
        }
    )
    
    # -------------------------------------------------------------------------
    # CHAMPS DE PROFIL
    # -------------------------------------------------------------------------
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom"
    )
    
    prenom = models.CharField(
        max_length=100,
        verbose_name="Prénom"
    )
    
    telephone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Téléphone"
    )
    
    # -------------------------------------------------------------------------
    # CHAMPS DE RÔLE ET PERMISSIONS
    # -------------------------------------------------------------------------
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='citoyen',
        verbose_name="Rôle"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Staff"
    )
    
    # -------------------------------------------------------------------------
    # CHAMPS OAUTH
    # -------------------------------------------------------------------------
    
    auth_provider = models.CharField(
        max_length=20,
        choices=AUTH_PROVIDER_CHOICES,
        blank=True,
        default='',
        verbose_name="Provider OAuth"
    )
    
    social_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID Social"
    )
    
    avatar_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL Avatar"
    )
    
    # -------------------------------------------------------------------------
    # TIMESTAMPS
    # -------------------------------------------------------------------------
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière connexion"
    )
    
    # -------------------------------------------------------------------------
    # CONFIGURATION DJANGO AUTH
    # -------------------------------------------------------------------------
    
    objects = UtilisateurManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom', 'telephone']
    
    # -------------------------------------------------------------------------
    # MÉTADONNÉES
    # -------------------------------------------------------------------------
    
    class Meta:
        db_table = 'utilisateurs'
        ordering = ['-created_at']
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    # -------------------------------------------------------------------------
    # MÉTHODES
    # -------------------------------------------------------------------------
    
    def __str__(self):
        """Représentation string de l'utilisateur."""
        return f"{self.prenom} {self.nom} ({self.get_role_display()})"
    
    def __repr__(self):
        """Représentation détaillée."""
        return f"<Utilisateur: {self.email} - {self.role}>"
    
    @property
    def nom_complet(self):
        """Retourne le nom complet formaté."""
        return f"{self.prenom} {self.nom}".strip()
    
    @property
    def is_citoyen(self):
        """Vérifie si l'utilisateur est un citoyen."""
        return self.role == 'citoyen'
    
    @property
    def is_agent(self):
        """Vérifie si l'utilisateur est un agent."""
        return self.role == 'agent'
    
    @property
    def is_admin(self):
        """Vérifie si l'utilisateur est un administrateur."""
        return self.role == 'administrateur'
    
    def clean(self):
        """Validation personnalisée."""
        super().clean()
        if self.email:
            self.email = self.email.lower().strip()
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_profile(self):
        """
        Retourne le profil associé selon le rôle.
        
        RETOURNE:
            Citoyen, Agent ou Administrateur selon le rôle
        """
        if self.is_citoyen:
            return getattr(self, 'citoyen_profile', None)
        elif self.is_agent:
            return getattr(self, 'agent_profile', None)
        elif self.is_admin:
            return getattr(self, 'admin_profile', None)
        return None
    
    def deactivate(self):
        """Désactive le compte."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
    
    def activate(self):
        """Active le compte."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


# ============================================================================
# MODÈLES DE PROFIL
# ============================================================================

class Citoyen(models.Model):
    """
    Profil spécifique d'un citoyen.
    
    RELATION: One-to-One avec Utilisateur
    
    CHAMPS:
        - utilisateur: Lien vers Utilisateur
        - Informations personnelles: date_naissance, lieu_naissance, cni_numero
        - Adresse: adresse, ville, code_postal
    """
    
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='citoyen_profile',
        primary_key=True
    )
    
    # Informations personnelles
    date_naissance = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de naissance"
    )
    
    lieu_naissance = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Lieu de naissance"
    )
    
    cni_numero = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro CNI"
    )
    
    # Adresse
    adresse = models.TextField(
        blank=True,
        verbose_name="Adresse"
    )
    
    ville = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Ville"
    )
    
    code_postal = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Code postal"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'citoyens'
        verbose_name = 'Citoyen'
        verbose_name_plural = 'Citoyens'
    
    def __str__(self):
        return f"Profil citoyen: {self.utilisateur.nom_complet}"


class Agent(models.Model):
    """
    Profil spécifique d'un agent administratif.
    
    RELATION: One-to-One avec Utilisateur
    
    CHAMPS:
        - utilisateur: Lien vers Utilisateur
        - Service: service assigné
        - Informations professionnelles: matricule, date_embauche
        - Disponibilité: est_disponible, charge_actuelle
    """
    
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='agent_profile',
        primary_key=True
    )
    
    # Service assigné (optionnel)
    service = models.ForeignKey(
        'Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agents'
    )
    
    # Informations professionnelles
    matricule = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Matricule"
    )
    
    date_embauche = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'embauche"
    )
    
    # Disponibilité
    est_disponible = models.BooleanField(
        default=True,
        verbose_name="Disponible"
    )
    
    charge_actuelle = models.PositiveIntegerField(
        default=0,
        verbose_name="Charge actuelle"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agents'
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
    
    def __str__(self):
        return f"Agent: {self.utilisateur.nom_complet}"
    
    def incrementer_charge(self):
        """Incrémente la charge de travail."""
        self.charge_actuelle += 1
        self.save(update_fields=['charge_actuelle', 'updated_at'])
    
    def decrementer_charge(self):
        """Décrémente la charge de travail."""
        if self.charge_actuelle > 0:
            self.charge_actuelle -= 1
            self.save(update_fields=['charge_actuelle', 'updated_at'])


class Administrateur(models.Model):
    """
    Profil spécifique d'un administrateur.
    
    RELATION: One-to-One avec Utilisateur
    """
    
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='admin_profile',
        primary_key=True
    )
    
    niveau_admin = models.CharField(
        max_length=20,
        choices=[
            ('super', 'Super Admin'),
            ('standard', 'Admin Standard'),
        ],
        default='standard',
        verbose_name="Niveau"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'administrateurs'
        verbose_name = 'Administrateur'
        verbose_name_plural = 'Administrateurs'
    
    def __str__(self):
        return f"Admin: {self.utilisateur.nom_complet}"


# ============================================================================
# MODÈLES MÉTIER: SERVICES ET DEMANDES
# ============================================================================

class Service(models.Model):
    """
    Service administratif proposé aux citoyens.
    
    EXEMPLES:
        - État Civil (actes de naissance, mariage, décès)
        - Urbanisme (permis de construire)
        - Finances (paiement taxes)
    
    CHAMPS:
        - nom, description
        - delai_traitement_jours: SLA
        - documents_requis: liste des documents nécessaires
        - est_actif: visibilité
    """
    
    id = models.AutoField(primary_key=True)
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom du service"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    delai_traitement_jours = models.PositiveIntegerField(
        default=7,
        verbose_name="Délai de traitement (jours)"
    )
    
    documents_requis = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Documents requis"
    )
    
    est_actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    ordre_affichage = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    tarif = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Tarif"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'services'
        ordering = ['ordre_affichage', 'nom']
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
    
    def __str__(self):
        return self.nom


class Demande(models.Model):
    """
    Demande administrative soumise par un citoyen.
    
    WORKFLOW DES STATUTS:
        brouillon → soumise → en_traitement → [traitee | rejetee] → archivee
                        ↓
                    en_attente (documents manquants)
    
    CHAMPS CLÉS:
        - numero_reference: Référence unique (ex: DEM-2024-000123)
        - citoyen: Demandeur
        - service: Service concerné
        - agent: Agent assigné (nullable)
        - status: Statut actuel
        - historique_statut: JSON avec historique des changements
    """
    
    # Statuts possibles
    STATUS_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumise', 'Soumise'),
        ('en_traitement', 'En traitement'),
        ('en_attente', 'En attente documents'),
        ('traitee', 'Traitée'),
        ('rejetee', 'Rejetée'),
        ('archivee', 'Archivée'),
    ]
    
    # Priorités
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('normal', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]
    
    id = models.AutoField(primary_key=True)
    
    # Référence unique
    numero_reference = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Référence"
    )
    
    # Relations
    citoyen = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='demandes',
        limit_choices_to={'role': 'citoyen'}
    )
    
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='demandes'
    )
    
    agent = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_assignees',
        limit_choices_to={'role': 'agent'}
    )
    
    # Contenu
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    
    description = models.TextField(
        verbose_name="Description"
    )
    
    type_document = models.CharField(
        max_length=50,
        verbose_name="Type de document"
    )
    
    # Statut et workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='brouillon',
        verbose_name="Statut"
    )
    
    historique_statut = models.JSONField(
        default=list,
        verbose_name="Historique des statuts"
    )
    
    # Priorité
    priorite = models.CharField(
        max_length=10,
        choices=PRIORITE_CHOICES,
        default='normal',
        verbose_name="Priorité"
    )
    
    # Dates importantes
    date_soumission = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de soumission"
    )
    
    date_debut_traitement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Début traitement"
    )
    
    date_cloture = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de clôture"
    )
    
    date_echeance = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'échéance"
    )
    
    # Compléments
    notes_internes = models.TextField(
        blank=True,
        verbose_name="Notes internes"
    )
    
    motif_rejet = models.TextField(
        blank=True,
        verbose_name="Motif de rejet"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'demandes'
        ordering = ['-created_at']
        verbose_name = 'Demande'
        verbose_name_plural = 'Demandes'
    
    def __str__(self):
        return f"{self.numero_reference} - {self.titre}"
    
    def save(self, *args, **kwargs):
        """Génère la référence si nouvelle demande."""
        if not self.numero_reference:
            self.numero_reference = self._generer_reference()
        super().save(*args, **kwargs)
    
    def _generer_reference(self):
        """Génère une référence unique."""
        from datetime import datetime
        now = datetime.now()
        count = Demande.objects.filter(
            created_at__year=now.year
        ).count() + 1
        return f"DEM-{now.year}-{count:06d}"
    
    @property
    def is_overdue(self):
        """Vérifie si la demande dépasse l'échéance."""
        if self.date_echeance and self.status not in ['traitee', 'rejetee', 'archivee']:
            return timezone.now() > self.date_echeance
        return False
    
    @property
    def duree_traitement(self):
        """Calcule la durée de traitement en jours."""
        if self.date_debut_traitement and self.date_cloture:
            return (self.date_cloture - self.date_debut_traitement).days
        if self.date_debut_traitement:
            return (timezone.now() - self.date_debut_traitement).days
        return None
    
    def changer_statut(self, nouveau_statut, modifie_par=None, raison=None):
        """
        Change le statut avec traçabilité.
        
        PARAMÈTRES:
            nouveau_statut: Nouveau statut
            modifie_par: ID de l'utilisateur modifiant
            raison: Raison du changement
        """
        ancien_statut = self.status
        
        # Enregistrer dans l'historique
        self.historique_statut.append({
            'from': ancien_statut,
            'to': nouveau_statut,
            'at': timezone.now().isoformat(),
            'by': modifie_par,
            'reason': raison
        })
        
        self.status = nouveau_statut
        self.save(update_fields=['status', 'historique_statut', 'updated_at'])


# ============================================================================
# MODÈLES MÉTIER: DOCUMENTS
# ============================================================================

class Document(models.Model):
    """
    Document attaché à une demande administrative.
    
    TYPES:
        - piece_identite: CNI, passeport
        - justificatif: Facture, contrat
        - formulaire: Formulaire administratif
        - attestation: Attestation officielle
    """
    
    TYPE_CHOICES = [
        ('piece_identite', 'Pièce d\'identité'),
        ('justificatif', 'Justificatif'),
        ('formulaire', 'Formulaire'),
        ('attestation', 'Attestation'),
        ('autre', 'Autre'),
    ]
    
    id = models.AutoField(primary_key=True)
    
    demande = models.ForeignKey(
        Demande,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    
    uploade_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='documents_uploades'
    )
    
    # Fichier
    fichier = models.FileField(
        upload_to='documents/%Y/%m/',
        verbose_name="Fichier"
    )
    
    fichier_nom = models.CharField(
        max_length=255,
        verbose_name="Nom original"
    )
    
    fichier_type = models.CharField(
        max_length=100,
        verbose_name="Type MIME"
    )
    
    fichier_taille = models.PositiveIntegerField(
        verbose_name="Taille (octets)"
    )
    
    # Métadonnées
    type_document = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        verbose_name="Type de document"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    est_verifie = models.BooleanField(
        default=False,
        verbose_name="Vérifié"
    )
    
    verifie_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_verifies'
    )
    
    date_verification = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de vérification"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
    
    def __str__(self):
        return f"{self.fichier_nom} ({self.get_type_document_display()})"
    
    @property
    def taille_readable(self):
        """Retourne la taille lisible (Ko, Mo)."""
        if self.fichier_taille < 1024:
            return f"{self.fichier_taille} o"
        elif self.fichier_taille < 1024 * 1024:
            return f"{self.fichier_taille / 1024:.1f} Ko"
        else:
            return f"{self.fichier_taille / (1024 * 1024):.1f} Mo"
    
    def marquer_verifie(self, agent):
        """Marque le document comme vérifié."""
        self.est_verifie = True
        self.verifie_par = agent
        self.date_verification = timezone.now()
        self.save(update_fields=['est_verifie', 'verifie_par', 'date_verification'])


# ============================================================================
# MODÈLES MÉTIER: TRAITEMENT (HISTORIQUE)
# ============================================================================

class Traitement(models.Model):
    """
    Action effectuée sur une demande (historique).
    
    ACTIONS POSSIBLES:
        - creation: Création de la demande
        - verification: Vérification des documents
        - assignation: Assignation à un agent
        - changement_statut: Changement de statut
        - commentaire: Ajout de commentaire
    """
    
    ACTION_CHOICES = [
        ('creation', 'Création'),
        ('verification', 'Vérification'),
        ('assignation', 'Assignation'),
        ('changement_statut', 'Changement de statut'),
        ('commentaire', 'Commentaire'),
        ('upload_document', 'Upload document'),
    ]
    
    id = models.AutoField(primary_key=True)
    
    demande = models.ForeignKey(
        Demande,
        on_delete=models.CASCADE,
        related_name='traitements'
    )
    
    agent = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='traitements_effectues',
        limit_choices_to={'role__in': ['agent', 'administrateur']}
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name="Action"
    )
    
    statut_precedent = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Statut précédent"
    )
    
    nouveau_statut = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Nouveau statut"
    )
    
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'traitements'
        ordering = ['-created_at']
        verbose_name = 'Traitement'
        verbose_name_plural = 'Traitements'
    
    def __str__(self):
        return f"{self.action} sur {self.demande.numero_reference}"


# ============================================================================
# MODÈLES MÉTIER: RENDEZ-VOUS
# ============================================================================

class RendezVous(models.Model):
    """
    Rendez-vous entre un citoyen et un agent.
    
    WORKFLOW:
        propose → confirme → realise
            ↓
        annule
    """
    
    STATUS_CHOICES = [
        ('propose', 'Proposé'),
        ('confirme', 'Confirmé'),
        ('realise', 'Réalisé'),
        ('annule', 'Annulé'),
        ('non_honore', 'Non honoré'),
    ]
    
    id = models.AutoField(primary_key=True)
    
    demande = models.ForeignKey(
        Demande,
        on_delete=models.CASCADE,
        related_name='rendez_vous'
    )
    
    citoyen = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='rdv_citoyen',
        limit_choices_to={'role': 'citoyen'}
    )
    
    agent = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='rdv_agent',
        limit_choices_to={'role': 'agent'}
    )
    
    # Date et heure
    date_rdv = models.DateField(
        verbose_name="Date du rendez-vous"
    )
    
    heure_debut = models.TimeField(
        verbose_name="Heure de début"
    )
    
    heure_fin = models.TimeField(
        verbose_name="Heure de fin"
    )
    
    # Détails
    lieu = models.CharField(
        max_length=200,
        verbose_name="Lieu"
    )
    
    motif = models.TextField(
        blank=True,
        verbose_name="Motif"
    )
    
    # Statut
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='propose',
        verbose_name="Statut"
    )
    
    # Dates importantes
    date_confirmation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de confirmation"
    )
    
    date_annulation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'annulation"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rendez_vous'
        ordering = ['date_rdv', 'heure_debut']
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
    
    def __str__(self):
        return f"RDV {self.date_rdv} - {self.citoyen.nom_complet}"
    
    def confirmer(self):
        """Confirme le rendez-vous."""
        self.status = 'confirme'
        self.date_confirmation = timezone.now()
        self.save(update_fields=['status', 'date_confirmation'])
    
    def annuler(self):
        """Annule le rendez-vous."""
        self.status = 'annule'
        self.date_annulation = timezone.now()
        self.save(update_fields=['status', 'date_annulation'])
    
    def marquer_realise(self):
        """Marque le rendez-vous comme réalisé."""
        self.status = 'realise'
        self.save(update_fields=['status'])


# ============================================================================
# MODÈLES MÉTIER: NOTIFICATIONS
# ============================================================================

class Notification(models.Model):
    """
    Notification envoyée à un utilisateur.
    
    TYPES:
        - info: Information générale
        - success: Action réussie
        - warning: Attention requise
        - error: Erreur
    
    DESTINATAIRES:
        - Citoyens: Sur événements de leurs demandes
        - Agents: Sur nouvelles demandes assignées
        - Admins: Sur alertes système
    """
    
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Succès'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur'),
    ]
    
    id = models.AutoField(primary_key=True)
    
    destinataire = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Contenu
    type_notification = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='info',
        verbose_name="Type"
    )
    
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    
    message = models.TextField(
        verbose_name="Message"
    )
    
    # Liens
    demande = models.ForeignKey(
        Demande,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    lien_action = models.URLField(
        blank=True,
        verbose_name="Lien d'action"
    )
    
    # État
    is_read = models.BooleanField(
        default=False,
        verbose_name="Lu"
    )
    
    date_lecture = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de lecture"
    )
    
    # Email envoyé?
    email_envoye = models.BooleanField(
        default=False,
        verbose_name="Email envoyé"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.titre} ({self.destinataire.email})"
    
    def marquer_lu(self):
        """Marque la notification comme lue."""
        self.is_read = True
        self.date_lecture = timezone.now()
        self.save(update_fields=['is_read', 'date_lecture'])


# ============================================================================
# MODÈLES MÉTIER: FAQ (CHATBOT)
# ============================================================================

class FAQ(models.Model):
    """
    Questions fréquentes pour le chatbot.
    
    UTILISATION:
        - Recherche par mots-clés
        - Suggestions automatiques
        - Statistiques d'utilisation
    """
    
    CATEGORIE_CHOICES = [
        ('general', 'Général'),
        ('inscription', 'Inscription'),
        ('demandes', 'Demandes'),
        ('documents', 'Documents'),
        ('rdv', 'Rendez-vous'),
        ('technique', 'Problème technique'),
    ]
    
    id = models.AutoField(primary_key=True)
    
    question = models.TextField(
        verbose_name="Question"
    )
    
    reponse = models.TextField(
        verbose_name="Réponse"
    )
    
    categorie = models.CharField(
        max_length=50,
        choices=CATEGORIE_CHOICES,
        default='general',
        verbose_name="Catégorie"
    )
    
    mots_cles = models.JSONField(
        default=list,
        verbose_name="Mots-clés"
    )
    
    compteur_utilisation = models.PositiveIntegerField(
        default=0,
        verbose_name="Utilisations"
    )
    
    est_actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'faq'
        ordering = ['categorie', 'question']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ'
    
    def __str__(self):
        return f"{self.categorie}: {self.question[:50]}..."
    
    def incrementer_utilisation(self):
        """Incrémente le compteur d'utilisation."""
        self.compteur_utilisation += 1
        self.save(update_fields=['compteur_utilisation'])


# ============================================================================
# FIN DES MODÈLES
# ============================================================================

"""
RÉSUMÉ DES RELATIONS:

Utilisateur (1) --- (0/1) Citoyen
Utilisateur (1) --- (0/1) Agent
Utilisateur (1) --- (0/1) Administrateur

Utilisateur (1) --- (N) Demande (citoyen)
Utilisateur (1) --- (N) Demande (agent assigné)

Service (1) --- (N) Demande
Service (1) --- (N) Agent

Demande (1) --- (N) Document
Demande (1) --- (N) Traitement
Demande (1) --- (N) RendezVous
Demande (1) --- (N) Notification

Utilisateur (1) --- (N) Document (upload)
Utilisateur (1) --- (N) Document (vérification)
Utilisateur (1) --- (N) Traitement
Utilisateur (1) --- (N) Notification
"""
