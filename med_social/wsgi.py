"""
WSGI config for med_social project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import newrelic.agent
import os
#import os.path as op

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "med_social.settings")
#os.environ['PYTHON_EGG_CACHE'] = op.join(op.dirname(op.abspath(
#    op.dirname(__file__))), '.python-eggs')

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.

parent_dir = os.path.dirname
root_dir = parent_dir(parent_dir(__file__))
newrelic_conf = os.path.join(root_dir, 'newrelic.ini')
if os.path.exists(newrelic_conf):
    newrelic.agent.initialize(newrelic_conf)


from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
