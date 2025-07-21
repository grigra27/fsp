"""
Production settings for Fair Sber Price
"""
import os
from .settings import *

# Override settings for production
DEBUG = False

# Add WhiteNoise middleware if available
try:
    import whitenoise
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    # Use CompressedStaticFilesStorage instead of CompressedManifestStaticFilesStorage
    # to avoid issues with missing source map files
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    # Additional WhiteNoise settings to handle missing files gracefully
    WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br', 'map']
    WHITENOISE_USE_FINDERS = True
except ImportError:
    pass

# Trust proxy headers from nginx
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database optimization for production
DATABASES['default'].update({
    'CONN_MAX_AGE': 60,
})

# Cache configuration for production (Redis recommended)
if os.getenv('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL'),
            'TIMEOUT': CACHE_TIMEOUT,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours

# No email configuration - using file logging only

# Performance optimizations
CONN_MAX_AGE = 60
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Additional security headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Logging for production - file-based only