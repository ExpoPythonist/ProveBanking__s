from django.conf.urls import patterns, url

from med_social.decorators import client_required

from . import views


urlpatterns = [
    url(r'^(?P<pk>\d+)/confirm_delete/$', client_required(views.ConfirmDeleteMetric.as_view()), name='confirm_delete'),
    url(r'^(?P<pk>\d+)/delete/$', client_required(views.DeleteMetric.as_view()), name='delete'),
    url(r'^(?P<pk>\d+)/delete/$', client_required(views.UndeleteMetric.as_view()), name='delete'),
]
