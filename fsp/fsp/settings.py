import os
from pathlib import Path
import logging.config
from dotenv import load_dotenv

from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file (check both project root and parent directory)
load_dotenv(BASE_DIR / '.env')  # Try project directory first
load_dotenv(BASE_DIR.parent / '.env')  # Try parent directory (repository root)

# Security
SECRET_KEY = os.getenv('SECRET_KEY', get_random_secret_key())
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
BOT_ONLY_MODE = os.getenv('BOT_ONLY_MODE', 'True').lower() == 'true'

# ALLOWED_HOSTS configuration
if DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
else:
    ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '').split(',') if host.strip()]
    # For Telegram bot, ALLOWED_HOSTS is not critical since it doesn't serve HTTP
    # Check if we're running the bot command
    import sys
    is_bot_command = len(sys.argv) > 1 and 'runtelegrambot' in sys.argv[1]
    
    if not ALLOWED_HOSTS and not is_bot_command:
        raise RuntimeError("ALLOWED_HOSTS environment variable is required for production web server!")

# Security settings for production
if not DEBUG:
    # SSL settings - disabled until SSL certificate is configured
    SECURE_SSL_REDIRECT = False  # Set to True when SSL certificate is configured
    SECURE_HSTS_SECONDS = 0  # Disable HSTS until SSL is configured
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    # Other security headers (safe to enable)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    # Cookie security - disabled until HTTPS is configured
    SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS
    CSRF_COOKIE_SECURE = False  # Set to True when using HTTPS

# Sber Configuration
SBER_STOCKS_QUANTITY = int(os.getenv('SBER_STOCKS_QUANTITY', '22586948000'))
CBR_BASE_URL = os.getenv('CBR_BASE_URL', 'https://www.cbr.ru/banking_sector/credit/coinfo/f123/')

# Cache Configuration - simple in-memory cache
CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '60'))  # 1 minute default


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'price.apps.PriceConfig',
    'telegrambot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fsp.urls'

TEMPLATES_DIR = BASE_DIR / 'templates'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
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

WSGI_APPLICATION = 'fsp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db' / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'ru-RU'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static_dev',
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache Configuration - simple in-memory
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'fsp-cache',
        'TIMEOUT': CACHE_TIMEOUT,
    }
}

# Logging Configuration - console only
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'price': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'telegrambot': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}
