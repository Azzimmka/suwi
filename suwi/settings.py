"""
Django settings for suwi project.
Суши love - Sushi Delivery Platform
"""

import os
from pathlib import Path

# Safe import for dj_database_url
try:
    import dj_database_url
    HAS_DJ_DATABASE_URL = True
except ImportError:
    HAS_DJ_DATABASE_URL = False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
# In production, set this via environment variable
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-dev-key-change-in-production'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,.railway.app').split(',')

# CSRF trusted origins for Railway
CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:8000,http://127.0.0.1:8000'
).split(',')


# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'apps.accounts',
    'apps.menu',
    'apps.cart',
    'apps.orders',
    'apps.telegram_bot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'suwi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processor for cart
                'apps.cart.context_processors.cart',
            ],
        },
    },
]

WSGI_APPLICATION = 'suwi.wsgi.application'


# =============================================================================
# DATABASE
# =============================================================================

# Use PostgreSQL in production (via DATABASE_URL), SQLite in development
if HAS_DJ_DATABASE_URL and os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# =============================================================================
# AUTHENTICATION
# =============================================================================

# Custom user model
AUTH_USER_MODEL = 'accounts.Customer'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.PhoneBackend',
    'django.contrib.auth.backends.ModelBackend',  # Fallback for admin
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Login settings
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'menu:catalog'
LOGOUT_REDIRECT_URL = 'menu:catalog'


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True


# =============================================================================
# STATIC FILES (CSS, JavaScript, Images)
# =============================================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise for serving static files in production
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# =============================================================================
# MEDIA FILES (User uploads)
# =============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# =============================================================================
# SESSION SETTINGS (for Cart)
# =============================================================================

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days
CART_SESSION_ID = 'cart'


# =============================================================================
# DEFAULT PRIMARY KEY
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================================
# TELEGRAM BOT SETTINGS
# =============================================================================

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')


# =============================================================================
# RESTAURANT SETTINGS
# =============================================================================

RESTAURANT_NAME = 'Суши love'
RESTAURANT_PHONE = '+998 XX XXX XX XX'
RESTAURANT_ADDRESS = 'Ташкент, ул. Примерная, 1'

# Restaurant coordinates for Yandex Go integration
RESTAURANT_LATITUDE = 41.311081
RESTAURANT_LONGITUDE = 69.240562


# =============================================================================
# SECURITY SETTINGS FOR PRODUCTION
# =============================================================================

if not DEBUG:
    # HTTPS settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # HSTS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
