# Chargement des dépendances
from pathlib import Path
import os
from dotenv import load_dotenv  

# Charger les variables d'environnement
load_dotenv()

# Définition du répertoire de base du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# 🔒 Clé secrète (stockée dans un fichier .env)
SECRET_KEY = os.getenv('SECRET_KEY')
# ⚠️ Activer/Désactiver le mode debug selon l'environnement
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# 🖥️ Hôtes autorisés
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",  # (si tu utilises Ngrok aussi)
    "administrateur.localhost",
    "votredomaine.com",  # Domaine principal
    "www.votredomaine.com",  # WWW
    "admin.votredomaine.com",  # Sous-domaine admin
    "127.0.0.1",
    "localhost",
]
SUBDOMAIN_URLCONFS = {
    None: "institut.urls",  # Domaine principal
    "admin": "administrateur.urls",  # Sous-domaine admin
}

# 🔐 Configuration de connexion et redirection
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
ROOT_URLCONF = 'institut.urls'

# 🏗️ Applications installées
INSTALLED_APPS = [
    'developpement',
    'administrateur',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'rest_framework',
    'rest_framework.authtoken', 
    'corsheaders',
]
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',  # Si vous utilisez les tokens
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Interface web
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}

# 🔑 Modèle utilisateur personnalisé
AUTH_USER_MODEL = 'developpement.CustomUser'

# ⚙️ Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "institut.middleware.SubdomainMiddleware",
]

# 📂 Configuration des templates
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

# 🌐 Configuration WSGI
WSGI_APPLICATION = 'institut.wsgi.application'

# 🛢️ Configuration de la base de données (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 🔑 Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 🌍 Paramètres de localisation
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

# 🎨 Fichiers statiques (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 🖼️ Configuration des fichiers média
AUTH_USER_MODEL = 'developpement.CustomUser'
LOGIN_REDIRECT_URL = 'espace_candidat'  # Redirection après login réussi
LOGIN_URL = 'candidat_login_page'           # URL de la page de login

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
import os

# Fichiers médias
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Configuration des fichiers uploadés
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# 📧 Configuration de l'email
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# 🖨 Vérification des paramètres email dans la console


# 🔒 Configuration de sécurité (désactivée temporairement pour les tunnels)
SECURE_SSL_REDIRECT = False  
SESSION_COOKIE_SECURE = False  
CSRF_COOKIE_SECURE = False  

# 🛡️ Configuration des domaines de confiance pour CSRF
CSRF_TRUSTED_ORIGINS = [
    "http://localhost", "http://127.0.0.1",
  # (si tu utilises Ngrok aussi)
]

# 📦 Configuration des proxys
if os.getenv('USE_PROXY', 'False') == 'True':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

# 🔄 Correction pour Django 4+
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/emails.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# settings.py
# Configuration Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"  # ou votre serveur SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = "votre.email@gmail.com"  # Remplacez par votre email
EMAIL_HOST_PASSWORD = "votre_mot_de_passe_app"  # Mot de passe d'application
DEFAULT_FROM_EMAIL = "votre.email@gmail.com"
SERVER_EMAIL = "votre.email@gmail.com"

# Configuration du site
SITE_NAME = "Institut de Formation"
SITE_URL = "http://127.0.0.1:8000"  # URL de votre site


# Configuration des cookies pour les sous-domaines
SESSION_COOKIE_DOMAIN = ".votredomaine.com"  # Notez le point au début
CSRF_COOKIE_DOMAIN = ".votredomaine.com"

# Forcer HTTPS en production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
