from django.views.generic import DetailView, ListView
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse

from med_social.views.base import BaseEditView

from .models import Note
from .forms import NoteForm, NoteCommentForm


class NoteDetailView(DetailView):
    model = Note
    template_name = 'notes/detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super(NoteDetailView, self).get_context_data(*args, **kwargs)
        context['comment_form'] = NoteCommentForm()
        context['related_content_object'] = self.object.content_object
        context['related_content_type'] = self.object.content_type
        return context


class NotesListView(ListView):
    model = Note
    template_name = 'notes/list.html'
    context_object_name = 'notes'

    def dispatch(self, *args, **kwargs):
        self.content_type = get_object_or_404(
            ContentType,
            model=self.kwargs['content_type'])

        self.content_object = get_object_or_404(
            self.content_type.model_class(),
            pk=self.kwargs['content_object_id'])
        self.user = self.request.user
        return super(NotesListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        qs = super(NotesListView, self).get_queryset()
        return qs.filter(object_id=self.content_object.pk)

    def get_context_data(self, *args, **kwargs):
        context = super(NotesListView, self).get_context_data(*args, **kwargs)
        context['related_content_object'] = self.content_object
        context['related_content_type'] = self.content_type
        return context


class CreateNoteView(BaseEditView):
    template_name = 'notes/create.html'
    model_form = NoteForm

    def dispatch(self, *args, **kwargs):
        self.content_type = get_object_or_404(
            ContentType,
            model=self.kwargs['content_type'])

        self.content_object = get_object_or_404(
            self.content_type.model_class(),
            pk=self.kwargs['content_object_id'])
        self.user = self.request.user
        return super(CreateNoteView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return self.content_object.get_absolute_url()

    def pre_save(self, instance):
        instance.content_object = self.content_object
        instance.posted_by = self.user
        return instance

    def get_context_data(self, *args, **kwargs):
        context = super(CreateNoteView, self).get_context_data(*args, **kwargs)
        context['related_content_object'] = self.content_object
        context['related_content_type'] = self.content_type
        return context


class CreateNoteCommentView(BaseEditView):
    model_form = NoteCommentForm

    def get(self, *args, **kwargs):
        return HttpResponseRedirect(self.note.get_absolute_url())

    def dispatch(self, request, pk):
        self.note = get_object_or_404(Note, id=pk)
        self.user = self.request.user
        return super(CreateNoteCommentView, self).dispatch(request,
                                                           pk)

    def get_success_url(self):
        return self.object.get_absolute_url()

    def pre_save(self, instance):
        instance.note = self.note
        instance.posted_by = self.user
        return instance

    def form_invalid(self, form):
        messages.error(self.request,
                       'Comment could not be posted because it was empyt.',
                       extra_tags='danger')
        return HttpResponseRedirect(self.note.get_absolute_url())

    def get_instance(self, *args, **kwargs):
        # Create only view. Does not need an Instance.
        return None
