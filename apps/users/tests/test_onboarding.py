from django.core.urlresolvers import reverse
from django.test.testcases import urlsplit
from django.contrib.auth import authenticate

from users.forms import PasswordSetForm
from .base import BaseUserTestCase


class OnboardingTestCase(BaseUserTestCase):
    def test_pending_steps_initialization(self):
        """
        Pending setup steps should be set according to user's kind
        upon user creation.
        """
        self.assertSequenceEqual(self.client_user.pending_setup_steps,
                                 self.client_user.SETUP_STEPS_CLIENT)
        self.assertSequenceEqual(self.vendor_user.pending_setup_steps,
                                 self.vendor_user.SETUP_STEPS_VENDOR)

    def test_non_setup_url_redirects_to_setup(self):
        """
        Non setup urls should redirect to setup urls if steps are pending.
        """
        self.client.login(username='john', password='foo')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlsplit(response.url).path,
            self.client_user.setup_step_url
        )

    def test_ajax_requests_not_redirected(self):
        """
        Ajax requests should not redirect to setup urls.
        """
        self.client.login(username='john', password='foo')
        response = self.client.get(
            reverse('users:all_notifications'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)

    def test_can_only_access_allowed_steps(self):
        """
        Client should not be able to access vendor steps.
        """
        self.client.login(username='john', password='foo')
        step = self.client_user.SETUP_STEPS_DICT[
            self.client_user.SETUP_VENDOR_PROFILE
        ]
        response = self.client.get(reverse(
            'user_setup:setup_step_%s' % step))
        self.assertEqual(response.status_code, 302)


class PasswordSetFormTestCase(BaseUserTestCase):
    def setUp(self):
        super(PasswordSetFormTestCase, self).setUp()

        step = self.client_user.SETUP_STEPS_DICT[
            self.client_user.SETUP_PASSWORD_SET
        ]
        path = reverse('user_setup:setup_step_%s' % step)
        self.form_kwargs = {
            'request': self.factory.post(path),
            'instance': self.client_user
        }

    def test_both_fields_required(self):
        """
        Both password fields are required.
        """
        form1 = PasswordSetForm(**self.form_kwargs)
        form2 = PasswordSetForm(
            data={'password1': 'foo'}, **self.form_kwargs)
        form3 = PasswordSetForm(
            data={'password2': 'foo'}, **self.form_kwargs)
        self.assertFalse(form1.is_valid(), msg='both fields absent')
        self.assertFalse(form2.is_valid(), msg='password2 absent')
        self.assertFalse(form3.is_valid(), msg='password1 absent')

    def test_passwords_should_match(self):
        """
        Both password fields are should have the same data.
        """
        form = PasswordSetForm(
            data={'password1': 'foo', 'password2': 'bar'}, **self.form_kwargs)
        self.assertFalse(form.is_valid())

    def test_form_valid_on_correct_data(self):
        """
        Form should validate when both passwords are identical.
        """
        form = PasswordSetForm(
            data={'password1': 'foo', 'password2': 'foo'}, **self.form_kwargs)
        self.assertTrue(form.is_valid())

    def test_password_set_on_save(self):
        form = PasswordSetForm(
            data={'password1': 'zxcv123', 'password2': 'zxcv123'},
            **self.form_kwargs
        )
        if form.is_valid():
            form.save()
        self.assertTrue(authenticate(
            username=self.client_user.username,
            password='zxcv123'))
