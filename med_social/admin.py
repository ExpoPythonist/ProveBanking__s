from django.contrib import admin
from django import forms
from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.conf import settings
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.admin import FlatPageAdmin, FlatpageForm

from redactor.widgets import RedactorEditor
from django.contrib.auth.models import Permission


Account = get_user_model()
csrf_protect_m = method_decorator(csrf_protect)


class FlatPageRedactorForm(forms.ModelForm):
    class Meta:
        model = FlatPage
        widgets = {'content': RedactorEditor()}
        exclude = ()


class MyFlatPageAdmin(admin.ModelAdmin):
    form = FlatPageRedactorForm


admin.site.unregister(FlatPage)
admin.site.register(FlatPage, MyFlatPageAdmin)

class VettedAdminSite(AdminSite):
    @never_cache
    def login(self, request, extra_context=None):
        """
        Displays the login form for the given HttpRequest.
        """
        from django.contrib.auth.views import login
        context = {
            'title': _('Log in'),
            'app_path': request.get_full_path(),
            REDIRECT_FIELD_NAME: settings.ADMIN_LOGIN_REDIRECT_URL,
        }
        context.update(extra_context or {})

        defaults = {
            'extra_context': context,
            'current_app': self.name,
            'authentication_form': self.login_form or AdminAuthenticationForm,
            'template_name': self.login_template or 'admin/login.html',
        }
        return login(request, **defaults)

site = VettedAdminSite()

# Disable celery admin
from djcelery.models import (TaskState, WorkerState,
                 PeriodicTask, IntervalSchedule, CrontabSchedule)

admin.site.register(Permission)
admin.site.unregister(TaskState)
admin.site.unregister(WorkerState)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(PeriodicTask)
