from django.conf.urls import patterns, url, include

from . import views


# namespace = posts
urlpatterns = [
    url(r'^$', views.post_list, name='post_list'),
    url(r'^(?P<pk>\d+)/$', views.post_view, name='post_view'),
]
