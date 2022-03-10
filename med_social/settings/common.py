# Django settings for med_social project.

import sys
import os
import os.path as op
from collections import OrderedDict

from .saml import SAML_CONFIG

PROJECT_ROOT = op.split(op.normpath(op.dirname(__file__)))[0]

PROJECT_PARENT = op.dirname(PROJECT_ROOT)
sys.path.insert(0, op.join(PROJECT_PARENT, 'vendor'))
sys.path.insert(0, op.join(PROJECT_PARENT, 'apps'))

RUNSERVERPLUS_SERVER_ADDRESS_PORT = '0.0.0.0:8000'

DEBUG = False
TEST_ENVIRONMENT = False

ADMINS = (
    ('Phil', 'john@proven.cc'),
    ('Max Filipenko', 'proven.test@yandex.ru')
)
SIGNUP_REVIEWERS = [
    'john@proven.cc',
    'proven.test@yandex.ru'
]
VERIFICATION_REVIEWERS = ['john@proven.cc', 'proven.test@yandex.ru', 'suzanne@proven.cc',
                          'jagdishpardhi@gmail.com']

DATABASE_ROUTERS = ('tenant_schemas.routers.TenantSyncRouter',)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                       # Or path to database file if using sqlite3.
        'USER': '',                       # Not used with sqlite3.
        'PASSWORD': '',                   # Not used with sqlite3.
        'HOST': '',                       # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                       # Set to empty string for default. Not used with sqlite3.
    },
    'OPTIONS': {
        'autocommit': True,
    },
}

SOUTH_DATABASE_ADAPTERS = {
    'default': 'south.db.postgresql_psycopg2',
}

MIGRATION_MODULES = {
    'auth': 'custom_migrations.auth',
    'watson': 'custom_migrations.watson'
}

CONN_MAX_AGE = 60 * 5

ALLOWED_HOSTS = ('.proven.cc',)
INTERNAL_IPS = ('127.0.0.1',)
SERVER_EMAIL = 'john@proven.cc'
HTTP_SCHEME = 'https'

SITE_INFO = {
    'NAME': 'Proven',
    'DOMAIN': 'proven.cc',
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)

EMAIL_REGEX = '''(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'''

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    CSRF_COOKIE_SECURE= True
    # session cookie secure works only under django 1.7.
    SESSION_COOKIE_SECURE = True

# Custom AUTH Model
AUTH_USER_MODEL = 'users.User'
ACCOUNT_USERNAME_REGEX = '[^\w+[\w+.-]*]'
ACCOUNT_PASSWORD_MIN_LENGTH = 8
ACCOUNT_PASSWORD_REGEX = '^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9]).{8,}$'

# timeout for authentication token, 1 day default
AUTH_TOKEN_TIMEOUT = 60 * 60 * 24 * 1
LOGIN_REDIRECT_URL = '/'
AUTHENTICATED_LOGIN_REDIRECTS = '/'
ADMIN_LOGIN_REDIRECT_URL = '/admin/users/user/'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'
UI_TIME_ZONE = 'US/Pacific'
DATE_FORMAT = "%d %B, %Y"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = op.join(PROJECT_ROOT, 'media')
INTERNAL_FILES_ROOT = op.join(MEDIA_ROOT, 'internal')
NETWORK_CLEANED_ROOT = op.join(INTERNAL_FILES_ROOT, 'cleaned')
NETWORK_RAW_ROOT = op.join(INTERNAL_FILES_ROOT, 'raw')

USE_PROTECTED_FILE_STORAGE = True

PROTECTED_ROOT = 'p'
MEDIA_URL = '/media/'

STATIC_ROOT = op.join(PROJECT_ROOT, 'static_collected')
STATIC_URL = 'https://proven-cc.s3.amazonaws.com/static/'

STATICFILES_DIRS = (
    op.join(PROJECT_ROOT, 'static'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.FileSystemFinder',
    'pipeline.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
    'pipeline.finders.CachedFileFinder',
)

ACCOUNT_ADAPTER = 'med_social.auth_adapters.AccountAdapter'
ACCOUNT_LOGOUT_ON_GET = True
RESTRICTED_ACCESS = True


VETTED_ICON = 'images/icon.png'

# AVATAR_GRAVATAR_BACKUP = False
# AUTO_GENERATE_AVATAR_SIZES = (35, 45, 80, 150)
AVATAR_AUTO_GENERATE_SIZES = (25, 35, 45, 80, 150)
AVATAR_MAX_SIZE = 1024 * 5120
AVATAR_GRAVATAR_BACKUP = False
AVATAR_DEFAULT_URL = 'images/defaults/avatar.jpg'
AVATAR_CLEANUP_DELETED = True


USER_PROFILE_IMAGE_FOLDER = 'images/users/'
COMPANY_LOGO_IMAGE_FOLDER = 'images/logo/'
COMPANY_BACKGROUND_IMAGE_FOLDER = 'images/background/'
COMPANY_BROCHURE_FOLDER = 'brochures/'
INSURANCE_FOLDER = 'insurance/'

# Redactor Editor
REDACTOR_OPTIONS = {
    'lang': 'en',
    'cleanUp': False,
    'convertDivs': False,
    'removeClasses': False,
}
REDACTOR_UPLOAD = 'uploads/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'test1234567890'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [
        os.path.join(PROJECT_ROOT, 'templates'),
    ],
    'OPTIONS': {
        'context_processors': [
            'django.core.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            "django.core.context_processors.request",
            'django.core.context_processors.debug',
            'django.core.context_processors.i18n',
            'django.core.context_processors.media',
            'django.core.context_processors.static',
            'django.core.context_processors.tz',
            'django.contrib.messages.context_processors.messages',
            'django_pjaxr.context_processors.pjaxr_information',
            'med_social.context_processors.constants',
            'med_social.context_processors.site_processor',
            'med_social.context_processors.tab_processor',
            'features.context_processors.features_processor',
            'users.context_processors.seo_metadata',
        ],
        'builtins': [
            'django_pjaxr.templatetags.pjaxr_extends',
        ],
        'debug': True
    },
}]
DEFAULT_PJAXR_TEMPLATE = "pjaxr.html"

AUTHENTICATION_BACKENDS = (
    "allauth.account.auth_backends.AuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
    "djangosaml2.backends.Saml2Backend",
)

MIDDLEWARE_CLASSES = (
    'tenant_schemas.middleware.TenantMiddleware',
    'raven.contrib.django.raven_compat.middleware.Sentry404CatchMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'med_social.middlewares.RestrictedAccessMiddleware',
    'mobi.middleware.MobileDetectionMiddleware',
    'med_social.middlewares.AjaxRedirectMiddleware',
    # Break Django Debug Toolbar. Need remove it or put into better place
    # 'django.middleware.gzip.GZipMiddleware',
    'pipeline.middleware.MinifyHTMLMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'med_social.urls'
PUBLIC_SCHEMA_URLCONF = 'med_social.public_urls'
PUBLIC_SCHEMA_NAME = 'public'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'med_social.wsgi.application'

PROVEN_APPS = (
    'features',
    'users',
    'med_social',

    'activity',
    'simple_activity',
    'categories',
    'divisions',
    'channels',
    'certs',
    'clients',
    'projects',
    'availability',
    'vendors',
    'reviews',
    'slas',
    'services',
    'notes',
    'locations',
    'posts',
    'roles',
    'rates',
    'analytics',
    'metrics',

    'lightrfp',

    # Make sure roles is the last app mentioned
    'ACL',
)

SHARED_APPS = (
    'django_atomic_signals',
    'django_atomic_celery',
    'customers',
    'aggregators',

    'polymorphic',
    'django.contrib.contenttypes',

    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.flatpages',
    'django.contrib.sites',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'autocomplete_light',

    # 'django.contrib.admindocs',
    'raven.contrib.django.raven_compat',

    # Third party apps
    'avatar',
    'mailviews',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.linkedin',
    'grappelli',
    'carton',
    'crispy_forms',
    'django_pjaxr',
    'django_extensions',
    'django_hstore',
    'django_premailer',
    'pipeline',
    'parsley',
    'post_office',
    'notifications',
    'rest_framework',
    'sorl.thumbnail',
    'taggit',
    # 'debug_toolbar',
    'djcelery',
    'bootstrap3',
    'redactor',
    'ordered_model',
    'masala',
    'django_jenkins',
    'storages',
    'colorfield',
    'generic_ct_tag',
    'watson',
    'import_export',
    # Our shared apps
    'blog',
)

SHARED_APPS = list(OrderedDict.fromkeys(SHARED_APPS + PROVEN_APPS))

TENANT_APPS = (
    # The following Django contrib apps must be in TENANT_APPS
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.flatpages',
    'django.contrib.sites',

    'avatar',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.linkedin',
    'djstripe',
    'notifications',
    'taggit',
    'watson',
    'djangosaml2',
)

# your tenant-specific apps
TENANT_APPS = list(OrderedDict.fromkeys(TENANT_APPS + PROVEN_APPS))

# Note: Migrations run in this order
INSTALLED_APPS = ['tenant_schemas'] + list(SHARED_APPS) + TENANT_APPS
INSTALLED_APPS = list(OrderedDict.fromkeys(INSTALLED_APPS))

TENANT_MODEL = "customers.Customer"
PG_EXTRA_SEARCH_PATHS = ['extensions']

# Jenkins
JENKINS_TASKS = (
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.django_tests',   # select one django or
    # 'django_jenkins.tasks.dir_tests'      # directory tests discovery
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pyflakes',
    # 'django_jenkins.tasks.run_jslint',
    'django_jenkins.tasks.run_jshint',
    'django_jenkins.tasks.run_csslint',
    'django_jenkins.tasks.run_sloccount',
    # 'django_jenkins.tasks.lettuce_tests',
)


# Tests
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Projects apps are tested by jenkins
PROJECT_APPS = PROVEN_APPS

# Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap3'

# Admin settings
GRAPPELLI_ADMIN_TITLE = 'Vetted Admin'
GRAPPELLI_AUTOCOMPLETE_LIMIT = 10

CACHES = {
    "default": {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:6379",
        "OPTIONS": {
            "CLIENT_CLASS": "redis_cache.client.DefaultClient",
        }
    }
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
    'PAGINATE_BY': 10,
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    )
}

RAVEN_CONFIG = {
    'dsn': 'https://something@app.getsentry.com/8662',
}

THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'level': 'ERROR',
            'class': 'logging.NullHandler',
        },
        'stdout': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.NullHandler'
            # Use commented settings in local config
            # 'class': 'logging.handlers.RotatingFileHandler',
            # 'filename': '/var/log/proven/django.log',
            # 'backupCount': 1024 * 1024 * 64
        }
    },
    'loggers': {
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['stdout'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'med_social': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False
        },
        'apps': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}


SIMPLE_ACTIVITY = {
    'ACTION_MODEL': 'activity.Action'
}


AUTH_KEYS = {
    'Twitter': {
        'CONSUMER_KEY' : '',
        'CONSUMER_SECRET' : "",
        'OAUTH_TOKEN' : "-",
        'OAUTH_TOKEN_SECRET' : "",
    },
    'Facebook': {
        'APP_ID': '',
        'APP_SECRET': '',
        'APP_DOMAIN': ''
    },
    'GOOGLE': {
        'KEY': '',
        'ID': '',
        'SECRET': '',
    }
}
MIXPANEL_API_TOKEN = '' 
MIXPANEL_ENABLED = False

ACCOUNT_EMAIL_SUBJECT_PREFIX = ''
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 15
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['https://www.googleapis.com/auth/userinfo.profile',
                  'https://www.googleapis.com/auth/userinfo.email',
                  'https://www.google.com/calendar/feeds/'],
        'AUTH_PARAMS': { 'access_type': 'offline' }
    },
    'linkedin': {
        'SCOPE': ['r_emailaddress', 'r_basicprofile']
    },
}

LINKEDIN_CLIENT_ID = '75c45nif6hq5v0'
LINKEDIN_CLIENT_SECRET = '2IsEot5vHC9cmhO6'


EMAIL_BACKEND = 'post_office.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'maxproven'
EMAIL_HOST_PASSWORD = 'iloveproven1'
DEFAULT_FROM_EMAIL = 'Proven <suzanne@proven.cc>'
NO_REPLY_EMAIL = '<noreply@proven.cc>'


#TODO: move this to local.py for installation specific settings
EMAIL_DOMAIN = 'http://localhost:8000'

DIFFBOT_TOKEN = ''

from .pipeline import *
from .celery_settings import *


#@FIXME I am a Hack
CC_EMAIL_TYPES = ['email_confirmation', 'welcome', 'email_confirmation_signup', 'accepted']

DEFAULT_HTTP_PROTOCOL = 'http://'

AWS_QUERYSTRING_AUTH = False
AWS_IS_GZIPPED = True
# AWS_S3_URL_PROTOCOL = 'https:'
AWS_PRELOAD_METADATA = False
AWS_HEADERS = {
    'Expires': 'Sat, 29 Apr 2035 13:31:45-0000 GMT',
    'Cache-Control': 'max-age=155520000, public'
}

AWS_STORAGE_BUCKET_NAME = 'proven-cc'
AWS_MEDIA_BUCKET_NAME = 'proven-cc'

# see http://developer.yahoo.com/performance/rules.html#expires

# STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
STATICFILES_STORAGE = 'med_social.custom_storages.S3PipelineStorage'
STATIC_PREFIX = 'static'
DEFAULT_FILE_STORAGE = 'med_social.custom_storages.S3FileStorage'
AVATAR_STORAGE = 'med_social.custom_storages.S3FileStorage'

THUMBNAIL_PRESERVE_FORMAT = True


# YAHOO BOSS
BOSS_KEY = '--'
BOSS_SECRET = ''

# FAROO News Search
FAROO_KEY = ''

HELLOSIGN_API_KEY = ''
HELLOSIGN_CLIENT_ID = ''

CLEARBIT_KEY = 'c867b3b92ef43bae2bf6e43318e4c729'  # '8e31f71329791ff12e3a72a160320205'


if DEBUG:
    PIPELINE['BROWSERIFY_ARGUMENTS'] = '-d'

#SAML config

#SAML_CONFIG = 'med_social.saml'
SAML_DJANGO_USER_MAIN_ATTRIBUTE = 'email'

SAML_CREATE_UNKNOWN_USER = True

CART_PRODUCT_MODEL = 'vendors.models.Vendor'
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', 'pk_test_8WtYoFKikKDRgPl71RJVvwjl')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_t8WcChd9xSPD0YoWR3Y99Nn6')
DJSTRIPE_PLANS = {
    'monthly-50': {
        'stripe_plan_id': 'monthly-50',
        'name': 'Proven Pro ($50/month)',
        'description': 'The monthly subscription plan to Proven',
        'price': 5000,  # $50.00
        'currency': 'usd',
        'interval': 'month',
    },
}

MAX_FILE_SIZE = 1024 * 1024 * 5
