from django.conf.urls import patterns, url

from roles import views
from med_social.decorators import admin_required

urlpatterns = [
    url(r'^$', admin_required(views.list_roles), name='list'),
    url(r'^create/$', admin_required(views.create_role), name='create'),
    url(r'^(?P<pk>\d+)/update/$', admin_required(views.update_role), name='edit'),
    url(r'^(?P<pk>\d+)/delete/$', admin_required(views.delete_role), name='delete'),
]
