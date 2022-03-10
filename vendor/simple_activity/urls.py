from django.conf.urls import patterns, url

urlpatterns = patterns('activity.views',
                       url(r'^event/(?P<content_id>\d+)/(?P<object_id>\d+)/$',
                           'event_update',
                           name='event_update'),
                       )
