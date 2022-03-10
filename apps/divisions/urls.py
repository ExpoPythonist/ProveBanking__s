from django.conf.urls import patterns, url, include

from . import views

urlpatterns = [
    url(r'^search/$', views.division_search, name='search'),
]
