from django.conf.urls import patterns, url, include

from .views.staffing import (change_staffing_acl, change_staffing_acl_vendors,
                             search_vendors_and_people)
from .views.projects import (create_proposed_resource, delete_proposed_resource, edit_proposed_resource,
                             change_proposed_status, proposed_resource_details, remove_proposed_resource)


urlpatterns = patterns('projects.views',
    url(r'^search/$', search_vendors_and_people, name='search'),
    url('(?P<request_pk>\d+)/propose/$', create_proposed_resource,
        name='propose'),
    url('(?P<request_pk>\d+)/acl/$', change_staffing_acl,
        name='change_acl'),
    url('(?P<request_pk>\d+)/acl/vendors/$', change_staffing_acl_vendors,
        name='change_acl_vendors'),
    url('proposed/(?P<pk>\d+)/delete/$', delete_proposed_resource,
        name='delete_proposed_resource'),
    url('proposed/(?P<pk>\d+)/edit/$', edit_proposed_resource,
        name='edit_proposed'),
    url(r'^proposed/(?P<pk>\d+)/status/$',
        change_proposed_status,
        name='change_proposed_status'
    ),
    url('proposed/(?P<pk>\d+)/$', proposed_resource_details,
        name='proposed_resource_details'
    ),
    url('proposed/(?P<pk>\d+)/remove/$', remove_proposed_resource,
        name='remove_proposed_resource'
    ),
    url(r'^r/', include('projects.requests_urls',
                        namespace='requests')),
)
