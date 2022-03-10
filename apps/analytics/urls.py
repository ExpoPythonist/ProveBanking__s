from django.conf.urls import patterns, url, include
from . import views


urlpatterns = [
    url(r'^$', views.home, name='analytics'),
    url(r'^peoplestaffed/$', views.peoplestaffed, name='peoplestaffed'),
    url(r'^cycletime/$', views.cycletime, name='cycletime'),
]
