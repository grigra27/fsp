"""
Production settings for Fair Sber Price - Simplified version
"""
import os
from .settings import *

# Override settings for production
DEBUG = False

# Add WhiteNoise middleware if available
try:
    import whitenoise
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br', 'map']
    WHITENOISE_USE_FINDERS = True
except ImportError:
    pass

# Trust proxy headers from nginx
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Use SQLite with optimizations
DATABASES['default'].update({
    'CONN_MAX_AGE': 60,
})

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Template caching
TEMPLATES[0]['APP_DIRS'] = False
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Performance settings
USE_ETAGS = True

# Security headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'