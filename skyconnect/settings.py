"""
Django settings for skyconnect project
"""

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / '.env'
load_dotenv(dotenv_path, encoding='utf-8')

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = True
ALLOWED_HOSTS = ['192.168.67.139', '127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'django_cleanup',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]
SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = 'accueil'
LOGOUT_REDIRECT_URL = 'accueil'
ROOT_URLCONF = 'skyconnect.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.logo_context',
                'core.context_processors.panier_count',
                'core.context_processors.menu_categories',
            ],
        },
    },
]

WSGI_APPLICATION = 'skyconnect.wsgi.application'

DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite') 
if DB_ENGINE == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-FR'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
            
STATIC_URL = 'static/' 
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False


# En DEV (pas en production)
SESSION_COOKIE_SECURE = False  # Pas HTTPS en local
CSRF_COOKIE_SECURE = False
DEBUG = True


LOGIN_REDIRECT_URL = 'accueil'
LOGOUT_REDIRECT_URL = 'accueil'

# Configuration django-allauth
ACCOUNT_LOGIN_METHODS = {'username', 'email'}  # Connexion avec username OU email
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']  # Champs requis pour l'inscription
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Désactivé car on utilise une vérification personnalisée
ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/300',  # 5 tentatives en 300 secondes (5 minutes)
}

# Débogage pour éviter la boucle infinie
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = 'email_confirmed_redirect'  # Redirection après confirmation
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = 'email_confirmed_redirect'  # Redirection si pas connecté

# Template pour les emails de confirmation
ACCOUNT_EMAIL_CONFIRMATION_URL = 'accounts/confirm-email/{{key}}/?user_id={{user.id}}'