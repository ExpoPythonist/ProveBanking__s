from django.apps import AppConfig
from django.utils.translation import ugettext as _

from . import models


class FeaturesConfig(AppConfig):
    name = 'features'
    verbose_name = "Features"

    def ready(self):
        models.financials = models.register(
            id=1, codename='financials', title=_('Financials'),
            description=_('Helps you track and manage finances.'))
        models.projects = models.register(
            id=2, codename='projects', title=_('Projects'),
            description=_('Project and staffing management.'))
        models.guides = models.register(
            id=3, codename='guides', title=_('Guides'),
            description=_('Collection of steps/forms to guide through a process.'))
        models.users = models.register(
            id=4, codename='contractors', title=_('Contractors'),
            description=_('contractor view'))
        models.proven_score = models.register(
            id=5, codename='proven_score', title=_('Proven Score'),
            description=_('Show Proven Score on vendor/client pages and send ranking emails.'))
        models.insurance = models.register(
            id=6, codename='insurance', title=_('Insurance'),
            description=_('Insurance upload and veritication.'))
        models.diversity = models.register(
            id=7, codename='diversity', title=_('Diversity'),
            description=_('Diversity management for vendors.'))
        models.rfp = models.register(
            id=8, codename='rfp', title=_('Requests for Proposals (RFP)'),
            description=_('Buyers send RFPs to vendors.'))
        '''
        models.sms = models.register(
            id=9, codename='sms', title=_('SMS Notifications'),
            description=_('Notify people through SMS.'))
        '''
        models.premium = models.register(
            id=10, codename='premium', title=_('Proven Premium'),
            description=_('Charge vendors for premium features (more invoice verifications).'))
        models.blog = models.register(
            id=11, codename='blog', title=_('Proven Blog'),
            description=_('Write and view blog posts.'))
