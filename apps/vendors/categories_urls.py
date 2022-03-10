from django.conf.urls import patterns, url

from med_social.decorators import member_required

from vendors.views import (CreateVendorSkill, VendorSkillList, DeleteVendorSkill)

# namespace = locations


urlpatterns = patterns('',
                       url(r'^(?P<pk>\d+)/create/$', member_required(CreateVendorSkill.as_view()),
                           name='create'),
                       url(r'^(?P<pk>\d+)/list/$', member_required(VendorSkillList.as_view()),
                           name='list'),
                       url(r'^(?P<pk>\d+)/delete/$', member_required(DeleteVendorSkill.as_view()), name='delete'),
                      )
