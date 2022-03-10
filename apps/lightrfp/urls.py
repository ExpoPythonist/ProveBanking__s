from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^@(?P<username>[\w+-]+)/requests/$', views.bid_list, name='bid_list'),
    # url(r'^@(?P<username>[\w+-]+)/requests/new/$', views.rfp_new, name='rfp_new'),
    url(r'^@(?P<username>[\w+-]+)/requests/(?P<uuid>[\w-]+)/$', views.rfp_view, name='rfp_view'),
    url(r'^@(?P<username>[\w+-]+)/requests/(?P<uuid>[\w-]+)/edit/$', views.rfp_edit, name='rfp_edit'),
    url(r'^@(?P<username>[\w+-]+)/requests/(?P<uuid>[\w-]+)/(?P<bid_uuid>[\w-]+)/$', views.rfp_view, name='rfp_view'),
    url(r'^@(?P<username>[\w+-]+)/bids/(?P<uuid>[\w-]+)/$', views.bid_view, name='bid_view'),
]
