from django import forms

from med_social.forms.mixins import FieldsetMixin
from .models import Note, NoteComment


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ('content',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(NoteForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''
        self.fields['content'].widget.attrs.update({
            'placeholder': 'Add new note',
            'class': 'textarea form-control',
        })

    def clean_content(self):
        if self.cleaned_data['content'].strip():
            return self.cleaned_data['content']
        else:
            raise forms.ValidationError('This field is required')


class NoteCommentForm(forms.ModelForm, FieldsetMixin):
    fieldsets = (
        ('',{ 'rows': (
            ('content',),
            ),
        }),
    )
    class Meta:
        model = NoteComment
        fields = ('content',)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(NoteCommentForm, self).__init__(*args, **kwargs)
        self.fields['content'].label = ''
        self.fields['content'].widget.attrs.update({
            'placeholder': 'Add new comment',
        })

    def clean_content(self):
        if self.cleaned_data['content'].strip():
            return self.cleaned_data['content']
        else:
            raise forms.ValidationError('This field is required')
