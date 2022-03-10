from django.conf.urls import patterns, url

from med_social.decorators import member_required

from vendors.views import (DiversityList, VendorDiversitySelect, VendorDiversityUpdate)

# namespace = services
urlpatterns = patterns('',
                       url(r'^(?P<pk>\d+)/list/$', member_required(DiversityList.as_view()),
                           name='list'),
                       url(r'^(?P<pk>\d+)/(?P<kind>\d+)/create/$', member_required(VendorDiversitySelect.as_view()),
                           name='create'),
                       url(r'^(?P<pk>\d+)/(?P<object_pk>\d+)/update/$', member_required(VendorDiversityUpdate.as_view()),
                           name='update'),)
