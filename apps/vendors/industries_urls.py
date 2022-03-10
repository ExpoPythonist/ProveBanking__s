from django.conf.urls import patterns, url

from med_social.decorators import member_required

from vendors import views

# namespace = locations


urlpatterns = patterns(
    '',
    url(r'^(?P<pk>\d+)/create/$', member_required(views.CreateVendorIndustry.as_view()), name='create'),
    url(r'^(?P<pk>\d+)/list/$', member_required(views.VendorIndustryList.as_view()), name='list'),
    url(r'^(?P<pk>\d+)/delete/$', member_required(views.DeleteVendorIndustry.as_view()), name='delete'),
)