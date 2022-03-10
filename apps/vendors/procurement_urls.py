from django.conf.urls import patterns, url

from med_social.decorators import member_required

from vendors.views import (CreateProcurementCateg, ProcurementCategoryList, DeleteVendorProcurement, VendorCustomPrimary)

# namespace = services
urlpatterns = patterns('',
                       url(r'^(?P<pk>\d+)/create/$', member_required(CreateProcurementCateg.as_view()),
                           name='create'),
                       url(r'^(?P<pk>\d+)/list/$', member_required(ProcurementCategoryList.as_view()),
                           name='list'),
                       url(r'^(?P<pk>\d+)/delete/$', member_required(DeleteVendorProcurement.as_view()), name='delete'),
                       url(r'^(?P<pk>\d+)/primary/$', member_required(VendorCustomPrimary.as_view()),
                           name='vendor_custom_primary'),
                      )
