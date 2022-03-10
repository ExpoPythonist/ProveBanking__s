from django.conf.urls import patterns, url

from med_social.decorators import client_required
from .. import views

urlpatterns = [
    url(r'^$', client_required(views.ServiceTypeList.as_view()), name='list'),
    url(r'^edit/(?P<pk>\d+)/$', client_required(views.EditServiceType.as_view()), name='edit'),
    url(r'^create/$', client_required(views.CreateServiceType.as_view()), name='create'),
]
