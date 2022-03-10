import os
from common import *
EXTRA_MIDDLEWARE_CLASSES = tuple()

DEBUG = False
TEMPLATE_DEBUG = DEBUG
REQUIRE_DEBUG = DEBUG
COMPRESS_ENABLED = True

PROJECT_ROOT = op.split(op.normpath(op.dirname(__file__)))[0]
PROJECT_PARENT = op.dirname(PROJECT_ROOT)

DATABASES = {
    'default': {
        'ENGINE': 'tenant_schemas.postgresql_backend',
        'NAME': 'productiondb',              # Or path to database file if using sqlite3.
        'USER': 'thevetted',                       # Not used with sqlite3.
        'PASSWORD': 'op1nrdm0l',                   # Not used with sqlite3.
        'HOST': 'production.c7ete0uese9p.us-east-1.rds.amazonaws.com', # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                       # Set to empty string for default. Not used with sqlite3.
        # 'OPTIONS': {
        #   'sslmode': 'require',
        #   'sslrootcert': os.path.join(PROJECT_PARENT, 'keys/RDS/rds-ssl-ca-cert.pem')
        # }
    }
}


BROKER_URL = 'redis://127.0.0.1:6379/1'

EMAIL_DOMAIN = 'http://proven.cc'

ALLOWED_HOSTS = ['127.0.0.1', '.proven.cc']
MIDDLEWARE_CLASSES += EXTRA_MIDDLEWARE_CLASSES
