from django.conf.urls import patterns, include, url

from med_social.decorators import vendor_required
from .status_views import (list_status, create_status, edit_status,
                           status_details, create_flow, edit_flow)


# namespace = locations
urlpatterns = patterns('projects.status_views',
    url(r'^$', list_status, name='list'),
    url(r'^create/$', create_status, name='create'),
    url(r'^(?P<status_pk>\d+)/edit/$', edit_status, name='edit'),
    url(r'^(?P<status_pk>\d+)/$', status_details, name='details'),
    url(r'^(?P<status_pk>\d+)/flow/add/$', create_flow,
        name='create_flow'),
    url(r'^flow/(?P<pk>\d+)/edit/$', edit_flow,
        name='edit_flow'),
)
