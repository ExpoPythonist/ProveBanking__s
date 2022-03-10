from django.conf.urls import patterns, url
from activity import views

urlpatterns = [
   url(r'^event/(?P<content_id>\d+)/(?P<object_id>\d+)/$', views.event_update, name='event_update'),
]
