from django.conf.urls import patterns, url

from med_social.decorators import member_required
from . import views

urlpatterns = [
    url(r'^$', member_required(views.GroupList.as_view()), name='list'),
    url(r'^create/$', member_required(views.GroupCreateView.as_view()), name='create'),
    url(r'^(?P<pk>\d+)/edit/$', member_required(views.GroupEditView.as_view()), name='edit'),
]
