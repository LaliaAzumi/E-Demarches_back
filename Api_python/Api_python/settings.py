"""
================================================================================
FICHIER: settings.py
PROJET: Api_python
RÔLE: Configuration Django globale

ARCHITECTURE:
    Configuration complète du projet Django avec:
    - Base de données PostgreSQL
    - Authentification JWT
    - OAuth (Google)
    - CORS
    - Email
    - Sécurité

ORGANISATION:
    1. Environnement (.env)
    2. Chemins (BASE_DIR)
    3. Sécurité (SECRET_KEY, DEBUG)
    4. Applications (INSTALLED_APPS)
    5. Middleware
    6. Base de données
    7. Authentification
    8. Internationalisation
    9. Statiques/Médias
    10. Logging

AGILE: Configuration = Infrastructure as Code
================================================================================
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# ============================================================================
# 1. CHARGEMENT ENVIRONNEMENT
# ============================================================================

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# ============================================================================
# 2. CHEMINS DE BASE
# ============================================================================

# Répertoire racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# 3. CONFIGURATION SÉCURITÉ
# ============================================================================

# Clé secrète (à changer en production !)
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-change-this-in-production-use-env-variable'
)

# Mode debug (False en production)
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Hôtes autorisés
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ============================================================================
# 4. APPLICATIONS DJANGO
# ============================================================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Requis pour django-allauth
]

THIRD_PARTY_APPS = [
    # REST Framework
    'rest_framework',
    'rest_framework.authtoken',
    
    # CORS
    'corsheaders',
    
    # JWT Authentication
    'rest_framework_simplejwt',
    
    # OAuth
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

LOCAL_APPS = [
    # Application métier principale
    'core.apps.CoreConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ============================================================================
# 5. MIDDLEWARE
# ============================================================================

MIDDLEWARE = [
    # Sécurité
    'django.middleware.security.SecurityMiddleware',
    
    # Sessions
    'django.contrib.sessions.middleware.SessionMiddleware',
    
    # CORS (doit être avant CommonMiddleware)
    'corsheaders.middleware.CorsMiddleware',
    
    # Django standards
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Allauth
    'allauth.account.middleware.AccountMiddleware',
]

# ============================================================================
# 6. ROUTAGE ET TEMPLATES
# ============================================================================

ROOT_URLCONF = 'Api_python.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Api_python.wsgi.application'

# ============================================================================
# 7. BASE DE DONNÉES (PostgreSQL)
# ============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'administratif_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'adri'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Connexion persistante (performance)
CONN_MAX_AGE = 60

# ============================================================================
# 8. VALIDATION MOTS DE PASSE
# ============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================================
# 9. MODÈLE UTILISATEUR PERSONNALISÉ
# ============================================================================

AUTH_USER_MODEL = 'core.Utilisateur'

# ============================================================================
# 10. CONFIGURATION REST FRAMEWORK
# ============================================================================

REST_FRAMEWORK = {
    # Authentification par défaut
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    
    # Permissions par défaut
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    # Pagination
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    
    # Throttling (protection rate limiting)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
    
    # Rendu JSON par défaut
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    
    # Filtres
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    
    # Gestion des exceptions
    'EXCEPTION_HANDLER': 'core.presentation.exceptions.custom_exception_handler',
}

# ============================================================================
# 11. CONFIGURATION JWT (SimpleJWT)
# ============================================================================

from datetime import timedelta

SIMPLE_JWT = {
    # Durée de vie des tokens
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    
    # Algorithme de signature
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    # Headers
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Claims
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    # Autres
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# ============================================================================
# 12. CONFIGURATION DJ-REST-AUTH
# ============================================================================

REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'jwt-auth',
    'JWT_AUTH_REFRESH_COOKIE': 'jwt-refresh-token',
    'JWT_AUTH_HTTPONLY': False,
    
    # Désactiver l'enregistrement (on utilise notre propre view)
    'REGISTER_SERIALIZER': 'core.presentation.serializers.RegisterSerializer',
}

# ============================================================================
# 13. CONFIGURATION DJANGO-ALLAUTH (OAuth)
# ============================================================================

SITE_ID = 1

# Configuration du compte
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Désactivé pour le dev

# Utiliser email comme champ username
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'email'

# Fournisseurs OAuth
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'METHOD': 'oauth2',
        'VERIFIED_EMAIL': True,
    }
}

# ============================================================================
# 14. CONFIGURATION CORS
# ============================================================================

# Autoriser toutes les origines en développement
CORS_ALLOW_ALL_ORIGINS = DEBUG

# En production, spécifier les origines autorisées
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Autoriser les credentials (cookies, headers d'authentification)
CORS_ALLOW_CREDENTIALS = True

# Headers autorisés
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Méthodes autorisées
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# ============================================================================
# 15. CONFIGURATION EMAIL
# ============================================================================

EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'  # Console en dev
)

# Configuration SMTP (production)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv(
    'DEFAULT_FROM_EMAIL',
    'Administratif <noreply@example.com>'
)

# ============================================================================
# 16. INTERNATIONALISATION
# ============================================================================

LANGUAGE_CODE = 'fr-fr'  # Français par défaut
TIME_ZONE = 'Africa/Dakar'  # Fuseau horaire Sénégal
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ============================================================================
# 17. FICHIERS STATIQUES ET MÉDIAS
# ============================================================================

# Fichiers statiques (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Fichiers médias (uploads utilisateurs)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Limite de taille des fichiers uploadés (10 Mo)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

# ============================================================================
# 18. LOGGING
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Créer le répertoire de logs s'il n'existe pas
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# ============================================================================
# 19. SÉCURITÉ SUPPLÉMENTAIRE (Production)
# ============================================================================

if not DEBUG:
    # HTTPS uniquement
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Cookies sécurisés
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Protection XSS
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # Clickjacking
    X_FRAME_OPTIONS = 'DENY'

# ============================================================================
# 20. CONFIGURATION PAR DÉFAUT POUR LE DÉVELOPPEMENT
# ============================================================================

# En développement, on simplifie certaines configurations
if DEBUG:
    # Désactiver certaines protections pour faciliter le dev
    CORS_ALLOW_ALL_ORIGINS = True
    
    # Email vers la console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    
    # Logging plus verbeux
    LOGGING['loggers']['django']['level'] = 'DEBUG'
    LOGGING['loggers']['core']['level'] = 'DEBUG'

# ============================================================================
# FIN DE LA CONFIGURATION
# ============================================================================

# Version de l'API
API_VERSION = '1.0.0'

# Nom de l'application
APP_NAME = 'Administratif API'
