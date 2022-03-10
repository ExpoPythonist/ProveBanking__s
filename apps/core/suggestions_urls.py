from django.conf.urls import patterns, url, include
from .views import suggestions


urlpatterns = [
    url(r'^tags/$', suggestions.tag_suggestions, name='tags'),
]
