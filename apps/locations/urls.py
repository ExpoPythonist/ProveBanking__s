from django.conf.urls import patterns, url, include

from . import views

urlpatterns = [
    url(r'^search/$', views.location_search, name='search'),
    url(r'^search/select/$', views.location_select_search, name='search_select'),
]
