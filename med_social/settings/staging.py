DEBUG = True
TEMPLATE_DEBUG = DEBUG
REQUIRE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'medsocial',              # Or path to database file if using sqlite3.
        'USER': 'medsocial',                       # Not used with sqlite3.
        'PASSWORD': 'medsocial',                   # Not used with sqlite3.
        'HOST': '127.0.0.1',                       # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                       # Set to empty string for default. Not used with sqlite3.
    }
}

SERVER_EMAIL = 'kevin@proven.cc'
#CELERY_EMAIL_BACKEND = 'masala.mail.backends.RedirectEmailBackend'
#REDIRECT_ALL_EMAIL_TO = 'kevin@proven.cc'
