from django.conf.urls import patterns, include, url
from . import views

urlpatterns = [
    url(r'^$', views.rate_list, name='list'),
    url(r'^(?P<pk>\d+)/$', views.rate_as_field, name='as_field'),
    url(r'^suggestions/$', views.suggestions, name='suggestions'),
    url(r'^create/$', views.create_rate, name='create'),
    #url(r'^user_rate/(?P<username>[\w\s@+.-]+)/$', views.edit_user_rate, name='edit_user_rate'),
    url(r'^(?P<pk>\d+)/edit/$', views.edit_rate, name='edit'),
    url(r'^(?P<pk>\d+)/delete/$', views.delete_rate, name='delete'),
]
