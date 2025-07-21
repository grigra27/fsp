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
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Sber Configuration
SBER_STOCKS_QUANTITY = int(os.getenv('SBER_STOCKS_QUANTITY', '22586948000'))
CBR_BASE_URL = os.getenv('CBR_BASE_URL', 'https://www.cbr.ru/banking_sector/credit/coinfo/f123/')

# Cache Configuration
CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '300'))  # 5 minutes default


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
    'price.middleware.PerformanceMonitoringMiddleware',
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
        'NAME': BASE_DIR / 'db.sqlite3',
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

TIME_ZONE = 'UTC'

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

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': CACHE_TIMEOUT,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Logging Configuration
LOG_DIR = BASE_DIR / 'logs'

# Create logs directory with proper permissions
try:
    LOG_DIR.mkdir(exist_ok=True, mode=0o755)
    # Test write permissions
    test_file = LOG_DIR / 'test.log'
    test_file.touch()
    test_file.unlink()
    LOGGING_AVAILABLE = True
except (PermissionError, OSError):
    LOGGING_AVAILABLE = False

# Configure logging based on availability
if LOGGING_AVAILABLE:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {asctime} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'app_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_DIR / 'app.log',
                'maxBytes': 1024*1024*5,  # 5MB
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_DIR / 'error.log',
                'maxBytes': 1024*1024*5,  # 5MB
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'console': {
                'level': 'DEBUG' if DEBUG else 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
        },
        'loggers': {
            'price': {
                'handlers': ['app_file', 'error_file', 'console'],
                'level': 'INFO',
                'propagate': False,
            },
            'telegrambot': {
                'handlers': ['app_file', 'error_file', 'console'],
                'level': 'INFO',
                'propagate': False,
            },
            'django': {
                'handlers': ['console', 'error_file'],
                'level': 'WARNING',
            },
            'django.request': {
                'handlers': ['error_file', 'console'],
                'level': 'ERROR',
                'propagate': False,
            },
        },
    }
else:
    # Fallback to console-only logging if file logging is not available
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
                'level': 'DEBUG' if DEBUG else 'INFO',
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
            'django.request': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': False,
            },
        },
    }
