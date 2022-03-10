from django.conf.urls import patterns, url

from med_social.decorators import member_required

from vendors.views import (CreateVendorService, VendorServicesList, DeleteVendorService)

# namespace = services
urlpatterns = patterns('',
                       url(r'^(?P<pk>\d+)/create/$', member_required(CreateVendorService.as_view()),
                           name='create'),
                       url(r'^(?P<pk>\d+)/list/$', member_required(VendorServicesList.as_view()),
                           name='list'),
                       url(r'^(?P<pk>\d+)/delete/$', member_required(DeleteVendorService.as_view()), name='delete'),
                      )
