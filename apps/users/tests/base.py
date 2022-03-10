from django.contrib.auth import get_user_model

from med_social.tests.base import TenantTestCase


class BaseUserTestCase(TenantTestCase):
    def setUp(self):
        super(BaseUserTestCase, self).setUp()
        user_model = get_user_model()
        self.client_user = user_model.objects.create_user(
            username='john', email='john@snow.com', first_name='John',
            last_name='Snow', kind=user_model.KIND_CLIENT, password='foo'
        )
        self.vendor_user = user_model.objects.create_user(
            username='robb', email='robb@stark.com', first_name='Robb',
            last_name='Stark', kind=user_model.KIND_VENDOR, password='foo'
        )

    def tearDown(self):
        # TODO: use transaction instead
        # get_user_model().objects.all().delete()
        super(BaseUserTestCase, self).tearDown()
