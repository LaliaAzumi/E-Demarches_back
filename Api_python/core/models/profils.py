"""
Modèles de profils : Citoyen, AgentAdministratif, Administrateur.
"""

from django.db import models, transaction
from django.db.models import Count, Q
from django.utils import timezone

from .mixins import ProfilMixin, TimestampMixin
from .exceptions import ValidationException, DemandeException, ProfilException


class Citoyen(ProfilMixin, TimestampMixin):
    """
    Profil citoyen avec fonctionnalités spécifiques.
    
    Attributs:
        cin: Numéro de carte d'identité (unique)
        adresse: Adresse du citoyen
    """
    
    id = models.AutoField(primary_key=True)
    cin = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="CIN")
    adresse = models.TextField(null=True, blank=True, verbose_name="Adresse")

    class Meta:
        db_table = 'citoyens'
        verbose_name = 'Citoyen'
        verbose_name_plural = 'Citoyens'

    def __str__(self) -> str:
        return f"Citoyen: {self.nom_complet}"
    
    def __repr__(self) -> str:
        return f"<Citoyen: {self.cin or 'N/A'} - {self.email}>"
    
    def clean(self):
        """Validation du CIN."""
        super().clean()
        if self.cin:
            # Nettoyer le CIN (enlever espaces et tirets)
            self.cin = self.cin.replace(' ', '').replace('-', '').upper()
            # Vérifier longueur minimale
            if len(self.cin) < 5:
                raise ProfilException("Le CIN doit contenir au moins 5 caractères", ProfilException.CIN_INVALIDE)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    # ========== Méthodes métier ==========
    
    def creer_demande(self, type_demande: str, service=None):
        """
        Crée une nouvelle demande administrative.
        
        Args:
            type_demande: Type de la demande
            service: Service administratif concerné
            
        Returns:
            DemandeAdministrative: La demande créée
        """
        from .demandes import DemandeAdministrative
        
        with transaction.atomic():
            demande = DemandeAdministrative.objects.create(
                citoyen=self,
                type_demande=type_demande,
                service=service
            )
            return demande
    
    def nombre_demandes_en_cours(self) -> int:
        """Compte les demandes en attente ou en cours."""
        from .demandes import DemandeAdministrative
        return self.demandes.filter(
            statut__in=[
                DemandeAdministrative.Statut.EN_ATTENTE, 
                DemandeAdministrative.Statut.EN_COURS
            ]
        ).count()
    
    def nombre_demandes_validees(self) -> int:
        """Compte les demandes validées."""
        from .demandes import DemandeAdministrative
        return self.demandes.filter(
            statut=DemandeAdministrative.Statut.VALIDEE
        ).count()
    
    def demandes_recentes(self, limite: int = 5):
        """Retourne les dernières demandes."""
        return self.demandes.order_by('-date_demande')[:limite]
    
    def a_rendez_vous_confirme(self) -> bool:
        """Vérifie si le citoyen a un rendez-vous confirmé."""
        from .rdv import RendezVous
        return self.rendez_vous.filter(statut=RendezVous.Statut.CONFIRME).exists()
    
    def prochain_rendez_vous(self):
        """Retourne le prochain rendez-vous confirmé."""
        from .rdv import RendezVous
        return self.rendez_vous.filter(
            statut=RendezVous.Statut.CONFIRME,
            proposition__date__gte=timezone.now().date()
        ).order_by('proposition__date', 'proposition__heure').first()


class AgentAdministratif(ProfilMixin, TimestampMixin):
    """
    Profil agent administratif avec méthodes métier.
    
    Attributs:
        matricule: Numéro matricule de l'agent (unique)
        service_affecte: Service où l'agent travaille
    """
    
    id = models.AutoField(primary_key=True)
    matricule = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        unique=True, 
        verbose_name="Matricule"
    )
    service_affecte = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name="Service affecté"
    )

    class Meta:
        db_table = 'agents'
        verbose_name = 'Agent administratif'
        verbose_name_plural = 'Agents administratifs'

    def __str__(self) -> str:
        return f"Agent: {self.nom_complet}"
    
    def __repr__(self) -> str:
        return f"<Agent: {self.matricule or 'N/A'} - {self.service_affecte}>"
    
    # ========== Méthodes métier ==========
    
    def traiter_demande(self, demande, nouveau_statut: str, commentaire: str = None):
        """
        Traite une demande et met à jour son statut.
        
        Args:
            demande: La demande à traiter
            nouveau_statut: Le nouveau statut à appliquer
            commentaire: Commentaire optionnel
            
        Returns:
            Traitement: L'objet traitement créé
        """
        from .documents import Traitement
        from .demandes import DemandeAdministrative
        
        # Vérifier que le statut est valide
        statuts_valides = [s[0] for s in DemandeAdministrative.Statut.choices]
        if nouveau_statut not in statuts_valides:
            raise DemandeException(
                f"Statut invalide: {nouveau_statut}",
                DemandeException.STATUT_INVALIDE,
                demande.id
            )
        
        with transaction.atomic():
            # Créer le traitement
            traitement = Traitement.objects.create(
                demande=demande,
                agent=self,
                commentaire=commentaire,
                statut_apres_traitement=nouveau_statut
            )
            
            # Mettre à jour la demande
            demande.changer_statut(nouveau_statut, commentaire)
            
            return traitement
    
    def proposer_rendez_vous(self, demande, date, heure, lieu: str = None):
        """
        Propose un créneau de rendez-vous.
        
        Args:
            demande: La demande concernée
            date: Date du rendez-vous
            heure: Heure du rendez-vous
            lieu: Lieu du rendez-vous
            
        Returns:
            PropositionRDV: La proposition créée
        """
        from .rdv import PropositionRDV
        from .demandes import DemandeAdministrative
        
        # Vérifier que la demande est validée
        if not demande.est_validee:
            raise DemandeException(
                "La demande doit être validée avant de proposer un RDV",
                DemandeException.STATUT_INVALIDE,
                demande.id
            )
        
        return PropositionRDV.objects.create(
            demande=demande,
            agent=self,
            date=date,
            heure=heure,
            lieu=lieu
        )
    
    def nombre_demandes_a_traiter(self) -> int:
        """Compte les demandes en attente."""
        from .demandes import DemandeAdministrative
        return DemandeAdministrative.objects.filter(
            statut=DemandeAdministrative.Statut.EN_ATTENTE
        ).count()
    
    def traitements_ce_mois(self) -> int:
        """Compte les traitements effectués ce mois."""
        now = timezone.now()
        return self.traitements.filter(
            date_traitement__month=now.month,
            date_traitement__year=now.year
        ).count()
    
    @classmethod
    def statistiques_traitements(cls):
        """
        Retourne les statistiques de traitement par agent.
        
        Returns:
            QuerySet: Agents avec annotations statistiques
        """
        from .documents import Traitement
        return cls.objects.annotate(
            total_traitements=Count('traitements'),
            validations=Count('traitements', 
                filter=Q(traitements__statut_apres_traitement='validee')),
            rejets=Count('traitements', 
                filter=Q(traitements__statut_apres_traitement='rejetee'))
        )


class Administrateur(ProfilMixin, TimestampMixin):
    """
    Profil administrateur système.
    
    Gère les utilisateurs, services et statistiques globales.
    """
    
    id = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'administrateurs'
        verbose_name = 'Administrateur'
        verbose_name_plural = 'Administrateurs'

    def __str__(self) -> str:
        return f"Admin: {self.nom_complet}"
    
    def __repr__(self) -> str:
        return f"<Administrateur: {self.email}>"
    
    # ========== Méthodes de gestion ==========
    
    def creer_agent(self, email: str, nom: str, prenom: str, 
                    telephone: str, password: str, **kwargs):
        """
        Crée un nouvel agent administratif.
        
        Args:
            email, nom, prenom, telephone: Informations de base
            password: Mot de passe
            **kwargs: Attributs supplémentaires pour AgentAdministratif
            
        Returns:
            AgentAdministratif: L'agent créé
        """
        from .utilisateur import Utilisateur
        
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
        from .utilisateur import Utilisateur
        try:
            user = Utilisateur.objects.get(id=utilisateur_id)
            user.desactiver()
        except Utilisateur.DoesNotExist:
            raise ProfilException("Utilisateur non trouvé")
    
    def reactiver_utilisateur(self, utilisateur_id: int):
        """Réactive un compte utilisateur."""
        from .utilisateur import Utilisateur
        try:
            user = Utilisateur.objects.get(id=utilisateur_id)
            user.reactiver()
        except Utilisateur.DoesNotExist:
            raise ProfilException("Utilisateur non trouvé")
    
    @classmethod
    def statistiques_globales(cls):
        """
        Retourne les statistiques globales du système.
        
        Returns:
            dict: Statistiques clés
        """
        from .utilisateur import Utilisateur
        from .demandes import DemandeAdministrative
        
        return {
            'total_utilisateurs': Utilisateur.objects.count(),
            'total_citoyens': Citoyen.objects.count(),
            'total_agents': AgentAdministratif.objects.count(),
            'total_administrateurs': cls.objects.count(),
            'demandes_en_attente': DemandeAdministrative.objects.filter(
                statut=DemandeAdministrative.Statut.EN_ATTENTE
            ).count(),
            'demandes_en_cours': DemandeAdministrative.objects.filter(
                statut=DemandeAdministrative.Statut.EN_COURS
            ).count(),
            'demandes_validees': DemandeAdministrative.objects.filter(
                statut=DemandeAdministrative.Statut.VALIDEE
            ).count(),
            'demandes_rejetees': DemandeAdministrative.objects.filter(
                statut=DemandeAdministrative.Statut.REJETEE
            ).count(),
        }
