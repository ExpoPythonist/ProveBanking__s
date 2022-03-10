from django.conf.urls import patterns, url

from med_social.decorators import member_required

from vendors.views import (CreateVendorRole, VendorRoleList, DeleteVendorRole)

# namespace = locations


urlpatterns = patterns('',
                       url(r'^(?P<pk>\d+)/create/$', member_required(CreateVendorRole.as_view()),
                       	   name='create'),
                       url(r'^(?P<pk>\d+)/list/$', member_required(VendorRoleList.as_view()),
                       	   name='list'),
                       url(r'^(?P<pk>\d+)/delete/$', member_required(DeleteVendorRole.as_view()), name='delete'),
                      )
