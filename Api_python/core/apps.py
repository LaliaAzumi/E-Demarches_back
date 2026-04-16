"""
================================================================================
FICHIER: apps.py
APPLICATION: core
RÔLE: Configuration de l'application Django

ARCHITECTURE:
    Définit la configuration de l'application 'core' qui contient
    toute la logique métier de la plateforme administrative.

    RESPONSABILITÉS:
        - Nom de l'application
        - Label pour l'admin
        - Signal handlers (ready())
        - Configuration des apps intégrées

AGILE: App Config = Application Setup
================================================================================
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuration de l'application Core.
    
    ATTRIBUTS:
        name: Nom Python de l'application
        label: Label pour l'interface admin
        verbose_name: Nom affiché
    
    MÉTHODES:
        ready: Appelée au démarrage de Django
    """
    
    # Nom complet de l'application (Python path)
    name = 'core'
    
    # Label pour les URL reverse et l'admin
    label = 'core'
    
    # Nom lisible pour l'interface d'administration
    verbose_name = 'Plateforme Administrative'
    
    def ready(self):
        """
        Méthode appelée lorsque l'application est prête.
        
        UTILISATION:
            - Enregistrement des signaux
            - Initialisation des caches
            - Vérification de la configuration
        
        ATTENTION: Cette méthode est appelée au démarrage de Django,
        donc éviter les imports lourds qui ralentiraient le boot.
        """
        # Import des signaux (à créer si nécessaire)
        # import core.signals
        
        # Log de démarrage
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Application 'core' initialisée avec succès")
        
        # Vérification de la configuration email
        from django.conf import settings
        if settings.DEBUG and 'console' in settings.EMAIL_BACKEND:
            logger.info("Mode DEBUG: Les emails seront envoyés vers la console")
        
        # Vérification de la configuration OAuth
        google_config = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
        if not google_config.get('APP', {}).get('client_id'):
            logger.warning("Configuration Google OAuth manquante")
        
        # Initialisation des services (lazy loading)
        # self._init_services()
    
    def _init_services(self):
        """
        Initialise les services de l'application.
        
        Cette méthode peut être utilisée pour:
        - Connecter les repositories aux modèles Django
        - Initialiser les caches
        - Démarrer des tâches planifiées
        """
        pass  # À implémenter si nécessaire
