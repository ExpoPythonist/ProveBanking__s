from django.conf.urls import patterns, url, include

from .views import BlogList

urlpatterns = patterns('',
    url(r'^(?P<kind>\w+)/$', BlogList.as_view(), name='list'),
)