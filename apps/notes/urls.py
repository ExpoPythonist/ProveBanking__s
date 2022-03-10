from django.conf.urls import patterns, url

from med_social.decorators import (client_required)
from . import views


urlpatterns = [
    url(r'^(?P<pk>\d+)/$', client_required(views.NoteDetailView.as_view()), name='detail'),
    url(r'^(?P<content_type>\w+)/(?P<content_object_id>\d+)/$', client_required(views.NotesListView.as_view()), name='list'),
    url(r'^create/(?P<content_type>\w+)/(?P<content_object_id>\d+)/$', client_required(views.CreateNoteView.as_view()), name='create'),
    url(r'^(?P<pk>\d+)/comment/$', client_required(views.CreateNoteCommentView.as_view()), name='post_comment'),
]
