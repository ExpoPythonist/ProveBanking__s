from django.conf.urls import patterns, url

# namespace

UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

urlpatterns = patterns('reviews.views',
    url(r'^(?P<content_type_pk>\d+)/(?P<object_pk>\d+)/review/$', 'review_object', name='add'),
    url(r'^(?P<review_pk>\d+)/$', 'review_details', name='detail'),
    url(r'^(?P<content_type_pk>\d+)/(?P<object_pk>\d+)/$', 'review_list', name='list'),
    url(r'^(?P<content_type_pk>\d+)/(?P<object_pk>\d+)/$', 'review_list', name='list'),
    url(r'^public/create/(?P<uuid>{})'.format(UUID), 'public_review',
        name='public_review'),
    url(r'^(?P<content_type_pk>\d+)/(?P<object_pk>\d+)/review_token/$',
        'create_review_token', name='create_review_token'),
)
