import os
from pathlib import Path
import dj_database_url
from django.core.exceptions import ImproperlyConfigured
import redis
import logging

# Set up logging for debugging
logger = logging.getLogger('django')

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Debug mode and security settings
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Security - Retrieve secret key from environment variables
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-only')  # Use environment variable in production

# Allowed hosts for the application
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,varsityplug-nvg2.onrender.com').split(',')

# Security settings - All SSL/HTTPS disabled for local development
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if not DEBUG else None
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else None
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
USE_X_FORWARDED_HOST = not DEBUG
USE_X_FORWARDED_PORT = not DEBUG
SECURE_BROWSER_XSS_FILTER = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = not DEBUG
X_FRAME_OPTIONS = 'SAMEORIGIN'

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://varsity-plug.onrender.com',
    'https://varsityplug-nvg2.onrender.com',  # Add your Render domain
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',  # WhiteNoise for static files
    'helper',  # Custom app
    'django_ratelimit',
]

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static file serving
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL and WSGI configuration
ROOT_URLCONF = 'varsity_plug.urls'
WSGI_APPLICATION = 'varsity_plug.wsgi.application'

# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'helper/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'helper_tags': 'helper.templatetags.helper_tags',
                'index_tags': 'helper.templatetags.index_tags',
                'helper_extras': 'helper.templatetags.helper_extras',
            },
        },
    },
]

# Database configuration - SQLite locally, PostgreSQL on Render
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise ImproperlyConfigured("DATABASE_URL environment variable is required in production.")
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True
        )
    }

# Cache configuration - Redis for production, DummyCache for development
REDIS_URL = os.getenv('REDIS_URL')
if not DEBUG and not REDIS_URL:
    logger.warning("REDIS_URL not set in production; falling back to locmem cache.")

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL or 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {'max_connections': 100},
        },
        'KEY_PREFIX': 'varsityplug'
    },
    'fallback': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'varsity-plug-fallback',
    }
}

if DEBUG or not REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
    SILENCED_SYSTEM_CHECKS = ['django_ratelimit.E003', 'django_ratelimit.W001']

# Check Redis availability for rate-limiting and sessions
RATELIMIT_CACHE = 'default'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache' if not DEBUG and REDIS_URL else 'django.contrib.sessions.backends.cached_db'

if not DEBUG and REDIS_URL:
    try:
        r = redis.Redis.from_url(REDIS_URL)
        r.ping()
        logger.info("Redis connection successful for rate-limiting and sessions")
    except (redis.ConnectionError, redis.RedisError) as e:
        logger.error(f"Redis connection failed: {str(e)}")
        logger.warning("Falling back to locmem cache for rate-limiting and cached_db for sessions")
        RATELIMIT_CACHE = 'fallback'
        SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Rate-limiting settings
RATELIMIT_CACHE_PREFIX = 'rl_'

# Session settings
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_TZ = True

# Static files (WhiteNoise)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # 1 year cache
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_REDIRECT_URL = 'helper:redirect_after_login'
LOGOUT_REDIRECT_URL = 'helper:home'
LOGIN_URL = '/login/'

# OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY and not DEBUG:
    logger.warning("OPENAI_API_KEY not set in production; AI chat functionality will be disabled.")

# Message tags for styling
from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'error',
}

# Logging configuration
# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

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
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'django.log'),
            'formatter': 'verbose',
            'mode': 'a',
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'error.log'),
            'formatter': 'verbose',
            'level': 'ERROR',
            'mode': 'a',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'helper': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}