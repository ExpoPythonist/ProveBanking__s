import os

from common import *

TEST_ENVIRONMENT = True
DEBUG = True
TEMPLATE_DEBUG = DEBUG
REQUIRE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'tenant_schemas.postgresql_backend',
        'NAME': 'vetted_test_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        #'HOST': '127.0.0.1',
        'HOST': os.environ.get('DB_PORT_5432_TCP_ADDR', '127.0.0.1'),
        'PORT': '5432',
    }
}

# Modify email backends for tests
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Update logging settings
LOGGING = None

# Setup testing of Celery tasks
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
#TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'


STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'

RAVEN_CONFIG = {
    'dsn': '',
}

USE_PROTECTED_FILE_STORAGE = False
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
AVATAR_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_URL = '/media/'

STATIC_URL = '/static/'
