from datetime import timedelta
from celery.schedules import crontab

BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/2'
CELERY_IGNORE_RESULT = False
CELERY_SEND_TASK_ERROR_EMAILS = False
CELERY_DEFAULT_QUEUE = 'default'
CELERY_DEFAULT_EXCHANGE = 'default'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'

CELERY_IMPORTS = (
    "med_social.tasks",
)

CELERY_QUEUES = {
    'default': {
        'exchange': 'default',
        'exchange_type': 'topic',
        'binding_key': 'task.#',
    },

    'aggregator': {
        'exchange': 'aggregator',
        'exchange_type': 'topic',
        'binding_key': 'aggregator.#'
    },
    'fast': {
        'exchange': 'fast',
        'exchange_type': 'topic',
        'binding_key': 'celery_fast.#'
    },
    'long': {
        'exchange': 'long',
        'exchange_type': 'topic',
        'binding_key': 'celery_long.#'
    }
}

CELERY_ROUTES = {
    'aggregator.tasks.*': {
        'queue': 'aggregator',
        'routing_key': 'aggregator.search'
    },
    'vendors.tasks.populate_vendors_clearbit_data': {
        'queue': 'long'
    }
}


#CELERYBEAT_SCHEDULE = {
    #'add-every-30-seconds': {
    #    'task': 'tasks.add',
    #    'schedule': timedelta(seconds=30),
    #    'args': (16, 16)
    #},
#}

CELERYBEAT_SCHEDULE = {
    'populate-clearbit': {
        'task': 'vendors.tasks.populate_vendors_clearbit_data',
        'schedule': timedelta(days=1),
        'args': ()
    }
}

CELERYD_PREFETCH_MULTIPLIER = 1


import djcelery
djcelery.setup_loader()
