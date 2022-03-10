import os

from common import *

EXTRA_MIDDLEWARE_CLASSES = tuple()

try:
    env = os.environ.get('DJANGO_ENV', 'local')
    exec('from %s import *' % env)
except ImportError, e:
    pass


if DEBUG:
    PIPELINE['BROWSERIFY_ARGUMENTS'] += ' -d'
    INSTALLED_APPS = INSTALLED_APPS  + ['debug_toolbar', ]

if 'TRAVIS' in os.environ:
    from .test import *
    from .travis import *


MIDDLEWARE_CLASSES += EXTRA_MIDDLEWARE_CLASSES
