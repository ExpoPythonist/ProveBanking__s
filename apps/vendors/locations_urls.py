from django.conf.urls import patterns, include, url

from med_social.decorators import member_required

from vendors.views import (CreateVendorLocation,
    EditVendorLocation, DeleteVendorLocation, VendorLocationList)

# namespace = locations


urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)/create/$', member_required(CreateVendorLocation.as_view()), name='create'),
    url(r'^(?P<pk>\d+)/list/$', member_required(VendorLocationList.as_view()), name='list'),
    url(r'^(?P<pk>\d+)/(?P<loc_pk>\d+)/edit/$', member_required(EditVendorLocation.as_view()), name='edit'),
    url(r'^(?P<pk>\d+)/delete/$', member_required(DeleteVendorLocation.as_view()), name='delete'),
    )
