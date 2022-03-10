from django.conf.urls import patterns, url
from . import views


urlpatterns = [
    url(r'(?P<content_type_pk>\d+)/(?P<object_pk>\d+)/create/$', views.create_channel, name='create'),
    url(r'^(?P<channel_pk>\d+)/$', views.channel_page, name='details'),
    url(r'^(?P<channel_pk>\d+)/users/invite/$', views.invite_user, name='invite_user'),
    url(r'^(?P<channel_pk>\d+)/comment/$', views.post_comment, name='comment'),
    url(r'^(?P<channel_pk>\d+)/suggestions.json/$', views.suggestions, name='suggestions'),
]
