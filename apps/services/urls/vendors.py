from django.conf.urls import patterns, url

from med_social.decorators import vendor_required
from .. import views

urlpatterns = [
    url(r'^add/$', vendor_required(views.AddServiceTypeContact.as_view()), name='add_contact'),
    url(r'^edit/(?P<pk>\d+)/$', vendor_required(views.EditServiceTypeContact.as_view()), name='edit_contact'),
]
