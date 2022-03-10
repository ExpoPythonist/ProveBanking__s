from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^search/$', views.client_search, name='search_basic'),
    url(r'^search/combined/$', views.client_search_combined, name='search'),
    url(r'^score/(?P<slug>[\w-]+)/$', views.score_estimate, name='score_estimate'),
]
