from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url(r'^search/news/$', views.SearchNews.as_view(), name='search_news'),
)
