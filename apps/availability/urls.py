from django.conf.urls import patterns, url


urlpatterns = patterns(
    'availability.views',
    url(r'^request/(?P<user_pk>\d+)/$', 'request_update', name='request_update'),
    url(r'^request/batch/$', 'batch_request_update', name='batch_request_update'),
    url(r'^confirm/$', 'confirm_availability', name='confirm'),
)
