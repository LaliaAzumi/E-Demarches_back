from django.db import models, transaction
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q, Count
import os


class TimestampMixin(models.Model):
    """Mixin abstrait pour ajouter des timestamps automatiques."""
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UtilisateurManager(BaseUserManager):
    """Manager personnalisé pour le modèle Utilisateur."""
    
    def create_user(self, email: str, nom: str, prenom: str, telephone: str, 
                    password: str = None, role: str = 'citoyen') -> 'Utilisateur':
        if not email:
            raise ValueError('L\'email est obligatoire')
        if not nom or not prenom:
            raise ValueError('Le nom et prénom sont obligatoires')
        
        email = self.normalize_email(email)
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

    def create_superuser(self, email: str, nom: str, prenom: str, 
                         telephone: str, password: str = None) -> 'Utilisateur':
        user = self.create_user(email, nom, prenom, telephone, password, role='administrateur')
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    
    def agents_actifs(self):
        """Retourne uniquement les agents actifs."""
        return self.filter(role='agent', is_active=True)
    
    def citoyens_inscrits(self):
        """Retourne les citoyens inscrits ce mois."""
        return self.filter(
            role='citoyen', 
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        )


class Utilisateur(AbstractBaseUser, PermissionsMixin, TimestampMixin):
    """Modèle utilisateur personnalisé avec authentification par email."""
    
    class Role(models.TextChoices):
        CITOYEN = 'citoyen', 'Citoyen'
        AGENT = 'agent', 'Agent administratif'
        ADMINISTRATEUR = 'administrateur', 'Administrateur'

    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UtilisateurManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom', 'telephone']

    class Meta:
        db_table = 'utilisateurs'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.prenom} {self.nom} ({self.get_role_display()})"
    
    def __repr__(self) -> str:
        return f"<Utilisateur: {self.email} - {self.role}>"
    
    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet formaté."""
        return f"{self.prenom} {self.nom}"
    
    @property
    def is_citoyen(self) -> bool:
        return self.role == self.Role.CITOYEN
    
    @property
    def is_agent(self) -> bool:
        return self.role == self.Role.AGENT
    
    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMINISTRATEUR
    
    def clean(self):
        """Validation personnalisée."""
        super().clean()
        if self.email:
            self.email = self.email.lower().strip()
        if self.telephone:
            self.telephone = self.telephone.strip()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def marquer_notifications_lues(self):
        """Marque toutes les notifications comme lues."""
        self.notifications.filter(lu=False).update(lu=True)
    
    def nombre_notifications_non_lues(self) -> int:
        return self.notifications.filter(lu=False).count()


class ProfilMixin(models.Model):
    """Mixin abstrait pour les profils liés à un utilisateur."""
    utilisateur = models.OneToOneField(
        Utilisateur, 
        on_delete=models.CASCADE,
        related_name='%(class)s_profile'
    )

    class Meta:
        abstract = True
    
    @property
    def email(self) -> str:
        return self.utilisateur.email
    
    @property
    def nom_complet(self) -> str:
        return self.utilisateur.nom_complet
    
    @property
    def telephone(self) -> str:
        return self.utilisateur.telephone


class Citoyen(ProfilMixin, TimestampMixin):
    """Profil citoyen avec fonctionnalités spécifiques."""
    
    id = models.AutoField(primary_key=True)
    cin = models.CharField(max_length=20, unique=True, null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'citoyens'

    def __str__(self) -> str:
        return f"Citoyen: {self.nom_complet}"
    
    def __repr__(self) -> str:
        return f"<Citoyen: {self.cin or 'N/A'} - {self.utilisateur.email}>"
    
    def creer_demande(self, type_demande: str, service=None) -> 'DemandeAdministrative':
        """Crée une nouvelle demande administrative."""
        with transaction.atomic():
            demande = DemandeAdministrative.objects.create(
                citoyen=self,
                type_demande=type_demande,
                service=service
            )
            return demande
    
    def nombre_demandes_en_cours(self) -> int:
        return self.demandes.filter(
            statut__in=[DemandeAdministrative.Statut.EN_ATTENTE, DemandeAdministrative.Statut.EN_COURS]
        ).count()
    
    def demandes_recentes(self, limite: int = 5):
        return self.demandes.order_by('-date_demande')[:limite]
    
    def a_rendez_vous_confirme(self) -> bool:
        return self.rendez_vous.filter(statut=RendezVous.Statut.CONFIRME).exists()


class AgentAdministratif(ProfilMixin, TimestampMixin):
    """Profil agent administratif avec méthodes métier."""
    
    id = models.AutoField(primary_key=True)
    matricule = models.CharField(max_length=50, null=True, blank=True, unique=True)
    service_affecte = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'agents'

    def __str__(self) -> str:
        return f"Agent: {self.nom_complet}"
    
    def __repr__(self) -> str:
        return f"<Agent: {self.matricule or 'N/A'} - {self.service_affecte}>"
    
    def traiter_demande(self, demande: 'DemandeAdministrative', 
                        nouveau_statut: str, commentaire: str = None) -> 'Traitement':
        """Traite une demande et met à jour son statut."""
        with transaction.atomic():
            traitement = Traitement.objects.create(
                demande=demande,
                agent=self,
                commentaire=commentaire,
                statut_apres_traitement=nouveau_statut
            )
            demande.statut = nouveau_statut
            demande.save()
            return traitement
    
    def proposer_rendez_vous(self, demande: 'DemandeAdministrative', 
                             date, heure, lieu: str = None) -> 'PropositionRDV':
        """Propose un créneau de rendez-vous."""
        return PropositionRDV.objects.create(
            demande=demande,
            agent=self,
            date=date,
            heure=heure,
            lieu=lieu
        )
    
    @classmethod
    def statistiques_traitements(cls):
        """Retourne les statistiques de traitement par agent."""
        return cls.objects.annotate(
            total_traitements=Count('traitements'),
            validations=Count('traitements', filter=Q(traitements__statut_apres_traitement='validee')),
            rejets=Count('traitements', filter=Q(traitements__statut_apres_traitement='rejetee'))
        )


class ServiceAdministratif(TimestampMixin):
    """Service administratif disponible."""
    
    id = models.AutoField(primary_key=True)
    nom_service = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    delai_traitement = models.IntegerField(help_text="Délai en jours", null=True, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'services_administratifs'
        ordering = ['nom_service']

    def __str__(self) -> str:
        return self.nom_service
    
    def __repr__(self) -> str:
        return f"<Service: {self.nom_service}>"
    
    @property
    def nombre_demandes_actives(self) -> int:
        return self.demandes.exclude(
            statut__in=[DemandeAdministrative.Statut.VALIDEE, DemandeAdministrative.Statut.REJETEE]
        ).count()


class DemandeAdministrative(TimestampMixin):
    """Demande administrative avec workflow complet."""
    
    class Type(models.TextChoices):
        CARTE_IDENTITE = 'carte_identite', 'Carte d\'identité'
        PASSEPORT = 'passeport', 'Passeport'
        ACTE_NAISSANCE = 'acte_naissance', 'Acte de naissance'
        ACTE_MARIAGE = 'acte_mariage', 'Acte de mariage'
        AUTRE = 'autre', 'Autre'

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        EN_COURS = 'en_cours', 'En cours'
        VALIDEE = 'validee', 'Validée'
        REJETEE = 'rejetee', 'Rejetée'

    id = models.AutoField(primary_key=True)
    id_demande = models.CharField(max_length=20, unique=True, null=True, blank=True)
    citoyen = models.ForeignKey(Citoyen, on_delete=models.CASCADE, related_name='demandes')
    service = models.ForeignKey(
        ServiceAdministratif, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='demandes'
    )
    type_demande = models.CharField(max_length=100, choices=Type.choices)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    motif_rejet = models.TextField(null=True, blank=True)
    date_demande = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'demandes'
        ordering = ['-date_demande']

    def __str__(self) -> str:
        return f"Demande #{self.id_demande or self.id} - {self.get_type_demande_display()}"
    
    def __repr__(self) -> str:
        return f"<Demande: {self.id} - {self.citoyen.nom_complet}>"
    
    def save(self, *args, **kwargs):
        if not self.id_demande:
            self.id_demande = self._generer_id()
        super().save(*args, **kwargs)
    
    def _generer_id(self) -> str:
        """Génère un ID unique pour la demande."""
        import random
        import string
        prefix = self.type_demande[:3].upper()
        suffix = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}-{suffix}"
    
    @property
    def est_en_attente(self) -> bool:
        return self.statut == self.Statut.EN_ATTENTE
    
    @property
    def est_validee(self) -> bool:
        return self.statut == self.Statut.VALIDEE
    
    @property
    def est_rejetee(self) -> bool:
        return self.statut == self.Statut.REJETEE
    
    def changer_statut(self, nouveau_statut: str, motif: str = None):
        """Change le statut avec validation."""
        if nouveau_statut not in [s[0] for s in self.Statut.choices]:
            raise ValidationError("Statut invalide")
        
        ancien_statut = self.statut
        self.statut = nouveau_statut
        
        if nouveau_statut == self.Statut.REJETEE and motif:
            self.motif_rejet = motif
        
        self.save()
        
        # Créer une notification
        Notification.objects.create(
            utilisateur=self.citoyen.utilisateur,
            type_notification='changement_statut',
            message=f"Votre demande {self.id_demande} est passée de '{ancien_statut}' à '{nouveau_statut}'"
        )
    
    def obtenir_documents(self):
        return self.documents.all()
    
    @classmethod
    def statistiques_par_statut(cls):
        """Statistiques des demandes par statut."""
        return cls.objects.values('statut').annotate(total=Count('id'))


class Document(TimestampMixin):
    """Document associé à une demande."""
    
    class Type(models.TextChoices):
        PDF = 'pdf', 'PDF'
        IMAGE = 'image', 'Image'
        DOC = 'doc', 'Document'
        AUTRE = 'autre', 'Autre'

    id = models.AutoField(primary_key=True)
    id_document = models.CharField(max_length=20, unique=True, null=True, blank=True)
    demande = models.ForeignKey(
        DemandeAdministrative, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    nom_document = models.CharField(max_length=255)
    type_document = models.CharField(max_length=50, choices=Type.choices, default=Type.AUTRE)
    fichier = models.FileField(upload_to='documents/%Y/%m/', null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    date_upload = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'documents'
        ordering = ['-date_upload']

    def __str__(self) -> str:
        return self.nom_document
    
    def __repr__(self) -> str:
        return f"<Document: {self.nom_document} - {self.type_document}>"
    
    def save(self, *args, **kwargs):
        if not self.id_document:
            self.id_document = f"DOC-{self.demande.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Déterminer le type à partir de l'extension
        if self.fichier and not self.type_document:
            ext = os.path.splitext(self.fichier.name)[1].lower()
            if ext in ['.pdf']:
                self.type_document = self.Type.PDF
            elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
                self.type_document = self.Type.IMAGE
            elif ext in ['.doc', '.docx']:
                self.type_document = self.Type.DOC
        
        super().save(*args, **kwargs)
    
    def supprimer_fichier(self):
        """Supprime le fichier physique et l'entrée en base."""
        if self.fichier and os.path.isfile(self.fichier.path):
            os.remove(self.fichier.path)
        self.delete()
    
    @property
    def taille_fichier(self) -> int:
        if self.fichier and os.path.exists(self.fichier.path):
            return os.path.getsize(self.fichier.path)
        return 0


class Traitement(TimestampMixin):
    """Traitement d'une demande par un agent."""
    
    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        EN_COURS = 'en_cours', 'En cours'
        VALIDEE = 'validee', 'Validée'
        REJETEE = 'rejetee', 'Rejetée'

    id = models.AutoField(primary_key=True)
    demande = models.ForeignKey(
        DemandeAdministrative, 
        on_delete=models.CASCADE, 
        related_name='traitements'
    )
    agent = models.ForeignKey(
        AgentAdministratif, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='traitements'
    )
    commentaire = models.TextField(null=True, blank=True)
    statut_apres_traitement = models.CharField(max_length=20, choices=Statut.choices, null=True, blank=True)
    date_traitement = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'traitements'
        ordering = ['-date_traitement']

    def __str__(self) -> str:
        return f"Traitement #{self.id} - {self.demande.id_demande}"
    
    def __repr__(self) -> str:
        return f"<Traitement: {self.id} - Agent: {self.agent}>"


class PropositionRDV(TimestampMixin):
    """Proposition de créneau rendez-vous."""
    
    class Statut(models.TextChoices):
        PROPOSE = 'propose', 'Proposé'
        CHOISI = 'choisi', 'Choisi'
        REFUSE = 'refuse', 'Refusé'
        EXPIRE = 'expire', 'Expiré'

    id = models.AutoField(primary_key=True)
    demande = models.ForeignKey(
        DemandeAdministrative, 
        on_delete=models.CASCADE, 
        related_name='propositions_rdv'
    )
    agent = models.ForeignKey(
        AgentAdministratif, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='propositions_rdv'
    )
    date = models.DateField()
    heure = models.TimeField()
    lieu = models.CharField(max_length=255, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PROPOSE)

    class Meta:
        db_table = 'propositions_rdv'
        verbose_name = 'Proposition RDV'
        verbose_name_plural = 'Propositions RDV'
        ordering = ['date', 'heure']

    def __str__(self) -> str:
        return f"RDV le {self.date} à {self.heure}"
    
    def __repr__(self) -> str:
        return f"<PropositionRDV: {self.date} {self.heure} - {self.statut}>"
    
    @property
    def datetime_complet(self):
        from datetime import datetime
        return datetime.combine(self.date, self.heure)
    
    def est_expire(self) -> bool:
        """Vérifie si la proposition est expirée."""
        from datetime import datetime
        return self.datetime_complet < timezone.now()
    
    def marquer_choisi(self):
        """Marque cette proposition comme choisie."""
        with transaction.atomic():
            self.statut = self.Statut.CHOISI
            self.save()
            
            # Refuser les autres propositions
            PropositionRDV.objects.filter(
                demande=self.demande
            ).exclude(id=self.id).update(statut=self.Statut.REFUSE)


class RendezVous(TimestampMixin):
    """Rendez-vous confirmé."""
    
    class Statut(models.TextChoices):
        CONFIRME = 'confirme', 'Confirmé'
        ANNULE = 'annule', 'Annulé'
        TERMINE = 'termine', 'Terminé'

    id = models.AutoField(primary_key=True)
    id_rendez_vous = models.CharField(max_length=20, unique=True, null=True, blank=True)
    proposition = models.OneToOneField(
        PropositionRDV, 
        on_delete=models.CASCADE, 
        related_name='rendez_vous'
    )
    citoyen = models.ForeignKey(
        Citoyen, 
        on_delete=models.CASCADE, 
        related_name='rendez_vous'
    )
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.CONFIRME)
    date_confirmation = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'rendez_vous'
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        ordering = ['-date_confirmation']

    def __str__(self) -> str:
        return f"RDV confirmé le {self.proposition.date}"
    
    def __repr__(self) -> str:
        return f"<RendezVous: {self.id_rendez_vous} - {self.statut}>"
    
    def save(self, *args, **kwargs):
        if not self.id_rendez_vous:
            self.id_rendez_vous = f"RDV-{timezone.now().strftime('%Y%m%d%H%M%S')}-{self.citoyen.id}"
        super().save(*args, **kwargs)
    
    def annuler(self, raison: str = None):
        """Annule le rendez-vous."""
        self.statut = self.Statut.ANNULE
        self.save()
        
        # Notifier le citoyen
        Notification.objects.create(
            utilisateur=self.citoyen.utilisateur,
            type_notification='rdv_confirme',
            message=f"Votre rendez-vous du {self.proposition.date} a été annulé. {raison or ''}"
        )
    
    def terminer(self):
        """Marque le rendez-vous comme terminé."""
        self.statut = self.Statut.TERMINE
        self.save()


class Notification(TimestampMixin):
    """Notification envoyée à un utilisateur."""
    
    class Type(models.TextChoices):
        CHANGEMENT_STATUT = 'changement_statut', 'Changement de statut'
        DOSSIER_PRET = 'dossier_pret', 'Dossier prêt'
        RDV_PROPOSE = 'rdv_propose', 'Rendez-vous proposé'
        RDV_CONFIRME = 'rdv_confirme', 'Rendez-vous confirmé'
        AUTRE = 'autre', 'Autre'

    id = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    message = models.TextField()
    type_notification = models.CharField(max_length=50, choices=Type.choices, default=Type.AUTRE)
    lu = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(default=timezone.now)
    date_lecture = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-date_envoi']

    def __str__(self) -> str:
        return f"Notification pour {self.utilisateur.nom_complet}: {self.message[:50]}..."
    
    def __repr__(self) -> str:
        return f"<Notification: {self.id} - {self.type_notification} - Lu: {self.lu}>"
    
    def marquer_lu(self):
        """Marque la notification comme lue."""
        if not self.lu:
            self.lu = True
            self.date_lecture = timezone.now()
            self.save(update_fields=['lu', 'date_lecture'])
    
    @classmethod
    def envoyer_a_tous(cls, utilisateurs, message: str, type_notif: str = 'autre'):
        """Envoie une notification à plusieurs utilisateurs."""
        notifications = [
            cls(utilisateur=u, message=message, type_notification=type_notif)
            for u in utilisateurs
        ]
        return cls.objects.bulk_create(notifications)


class Administrateur(ProfilMixin, TimestampMixin):
    """Profil administrateur système."""
    
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'administrateurs'

    def __str__(self) -> str:
        return f"Admin: {self.nom_complet}"
    
    def __repr__(self) -> str:
        return f"<Administrateur: {self.utilisateur.email}>"
    
    def creer_agent(self, email: str, nom: str, prenom: str, 
                    telephone: str, password: str, **kwargs) -> AgentAdministratif:
        """Crée un nouvel agent."""
        with transaction.atomic():
            user = Utilisateur.objects.create_user(
                email=email,
                nom=nom,
                prenom=prenom,
                telephone=telephone,
                password=password,
                role=Utilisateur.Role.AGENT
            )
            return AgentAdministratif.objects.create(utilisateur=user, **kwargs)
    
    def desactiver_utilisateur(self, utilisateur_id: int):
        """Désactive un compte utilisateur."""
        user = Utilisateur.objects.get(id=utilisateur_id)
        user.is_active = False
        user.save()
    
    @classmethod
    def statistiques_globales(cls):
        """Retourne les statistiques globales du système."""
        return {
            'total_utilisateurs': Utilisateur.objects.count(),
            'total_citoyens': Citoyen.objects.count(),
            'total_agents': AgentAdministratif.objects.count(),
            'demandes_en_attente': DemandeAdministrative.objects.filter(
                statut=DemandeAdministrative.Statut.EN_ATTENTE
            ).count(),
            'demandes_validees': DemandeAdministrative.objects.filter(
                statut=DemandeAdministrative.Statut.VALIDEE
            ).count(),
        }


class FAQChatbot(TimestampMixin):
    """FAQ pour le chatbot d'assistance."""
    
    id = models.AutoField(primary_key=True)
    question = models.TextField()
    reponse = models.TextField()
    mots_cles = models.CharField(max_length=255, blank=True, help_text="Mots-clés séparés par des virgules")
    categorie = models.CharField(max_length=100, blank=True)
    ordre_affichage = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = 'faq_chatbot'
        ordering = ['ordre_affichage', 'question']
        verbose_name = 'FAQ Chatbot'
        verbose_name_plural = 'FAQs Chatbot'

    def __str__(self) -> str:
        return f"FAQ: {self.question[:50]}..."
    
    def __repr__(self) -> str:
        return f"<FAQChatbot: {self.categorie} - {self.question[:30]}>"
    
    def get_mots_cles_list(self) -> list:
        """Retourne la liste des mots-clés."""
        return [mot.strip() for mot in self.mots_cles.split(',') if mot.strip()]
    
    @classmethod
    def rechercher(cls, query: str):
        """Recherche dans les FAQs par mots-clés ou question."""
        return cls.objects.filter(
            Q(question__icontains=query) | 
            Q(reponse__icontains=query) |
            Q(mots_cles__icontains=query),
            actif=True
        )
    
    @classmethod
    def par_categorie(cls, categorie: str):
        """Retourne les FAQs d'une catégorie."""
        return cls.objects.filter(categorie=categorie, actif=True)

