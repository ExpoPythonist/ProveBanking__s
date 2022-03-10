import json

from django import forms
from django.conf import settings
from django.db.models import FileField
from django.forms import ModelChoiceField
from django.forms.utils import flatatt
from django.template.defaultfilters import filesizeformat
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from rest_framework.relations import RelatedField


class TextGroupInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        self.prepend = kwargs.pop('prepend', None)
        self.append = kwargs.pop('append', None)
        super(TextGroupInput, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_text(self._format_value(value))
        widget = '<div class="input-group">'
        if self.prepend:
            widget += '<span class="input-group-addon">' + self.prepend + '</span>'
        widget += '<input{0}/>'
        if self.append:
            widget += '<span class="input-group-addon">' + self.append + '</span>'
        widget += '</div>'
        return format_html(widget, flatatt(final_attrs))


class SelectizeInput(forms.Select):
    def __init__(self, *args, **kwargs):
        self.native_on_mobile = kwargs.pop('native_on_mobile', False)
        super(SelectizeInput, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = ''
        if value:
            try:
                obj = self.model.objects.get(id=value)
            except (self.model.DoesNotExist, ValueError):
                obj = value
        else:
            obj = value
        attrs = attrs or {}
        if self.native_on_mobile:
            attrs['ignore-enhance-mobile'] = True
        attrs['data-selectize'] = 'yes'
        final_attrs = self.build_attrs(attrs, name=name)
        output = [format_html('<select{0}>', flatatt(final_attrs))]
        if self.choices:
            for k, v in self.choices:
                if str(k) == str(value):
                    output.append('<option value="%s" selected="selected">%s</option>' % (k, v))
                else:
                    output.append('<option value="%s">%s</option>' % (k, v))
        elif value:
            output.append('<option value="%s" selected="selected">%s</option>' % (value, obj))
        output.append('</select>')
        return mark_safe('\n'.join(output))


class SelectizeMultiInput(forms.SelectMultiple):
    def __init__(self, *args, **kwargs):
        self.native_on_mobile = kwargs.pop('native_on_mobile', False)
        super(SelectizeMultiInput, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, choices=()):
        value = value or []
        attrs = attrs or {}
        if self.native_on_mobile:
            attrs['ignore-enhance-mobile'] = True
        attrs['multiple'] = 'multiple'
        attrs['data-selectize'] = 'yes'
        final_attrs = self.build_attrs(attrs, name=name)
        output = [format_html('<select{0}>', flatatt(final_attrs))]
        if isinstance(value, basestring):
            value = value.split(',')
        else:
            value = [str(v) for v in value]
        if self.choices:
            for k, v in self.choices:
                if str(k) in value:
                    output.append('<option value="%s" selected="selected">%s</option>' % (k, v))
                else:
                    output.append('<option value="%s">%s</option>' % (k, v))
        else:
            if value:
                try:
                    objs = self.model.objects.filter(id__in=value)
                except ValueError:
                    objs = []
            else:
                objs = []
            for obj in objs:
                output.append('<option value="%s" selected="selected">%s</option>' % (obj.pk, obj))
        output.append('</select>')
        return mark_safe('\n'.join(output))


class SelectizeModelField(forms.ChoiceField):
    widget = SelectizeInput

    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model', None)
        self.create_func = kwargs.pop('create_func', None)
        super(SelectizeModelField, self).__init__(*args, **kwargs)
        self.widget.model = self.model
        self.widget.choices = list(kwargs.get('choices', tuple()))
        if self.create_func:
            self.widget.attrs['selectize-create'] = True
        self.help_text = kwargs.get('help_text', ' ')

    def valid_value(self, value):
        return True

    def clean(self, value):
        super(SelectizeModelField, self).clean(value)
        if isinstance(value, basestring):
            value = value.strip()
        try:
            return self.model.objects.get(id=value)
        except (self.model.DoesNotExist, ValueError):
            if self.create_func:
                return self.create_func(value)
            else:
                raise forms.ValidationError('The provided value is not a valid'
                                            ' choice')


class MultiSelectizeModelField(forms.ModelMultipleChoiceField):
    widget = SelectizeMultiInput

    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model', None)
        self.create_func = kwargs.pop('create_func', None)
        self.max_length = kwargs.pop('max_length', None)
        super(MultiSelectizeModelField, self).__init__(*args, **kwargs)
        if self.create_func:
            self.widget.attrs['selectize-create'] = True
        if self.max_length:
            self.widget.attrs['selectize-maxItems'] = self.max_length
        self.help_text = kwargs.get('help_text', ' ')


class MultiWidget(forms.MultiWidget):
    def decompress(self, value):
        if value:
            return value.split(',')
        else:
            return []


class MultiSelectChooser(forms.MultiValueField):
    def __init__(self, *args, **kwargs):
        self.short_help_text = kwargs.pop('short_help_text', '')
        self.max_length = kwargs.pop('max_length')
        self.choices = kwargs.pop('choices', [])
        self.choices = [('', '',)] + list(self.choices)
        kwargs['fields'] = [forms.CharField() for i in range(self.max_length)]
        kwargs['widget'] = MultiWidget(widgets=[forms.Select(choices=self.choices) for i in range(self.max_length)],
                                       attrs={'class': 'multi-select'})
        super(MultiSelectChooser, self).__init__(*args, **kwargs)

    def compress(self, clean_data):
        return ','.join(clean_data)

    def clean(self, value):
        try:
            return [int(v) for v in value if v]
        except ValueError:
            raise forms.ValidationError('Must be a sequence of integers')


class SwitchInput(forms.widgets.CheckboxInput):
    def __init__(self, *args, **kwargs):
        self.switch_attrs = kwargs.pop('switch_attrs', {})
        super(SwitchInput, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        checkbox = super(SwitchInput, self).render(name, value, attrs)
        switch = u'<div class="make-switch">%s</div>' % checkbox
        return switch


class ContentTypeRestrictedFileField(FileField):
    """
    Same as FileField, but you can specify:
        * content_types - list containing allowed content_types. Example: ['application/pdf', 'image/jpeg']
        * max_upload_size - a number indicating the maximum file size allowed for upload.
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB 104857600
            250MB - 214958080
            500MB - 429916160
    """
    def __init__(self, content_types=None, max_upload_size=None, **kwargs):
        self.content_types = content_types or []
        self.max_upload_size = max_upload_size
        super(ContentTypeRestrictedFileField, self).__init__(**kwargs)

    def clean(self, *args, **kwargs):
        data = super(ContentTypeRestrictedFileField, self).clean(*args, **kwargs)

        file = data.file
        content_type = file.content_type

        if content_type in self.content_types:
            if self.max_upload_size and (file._size > self.max_upload_size):
                raise forms.ValidationError(_('Please keep filesize under %s. Current filesize %s') % (filesizeformat(self.max_upload_size), filesizeformat(file._size)))
        else:
            raise forms.ValidationError(_('Filetype not supported.'))

        return data


class LazyModelChoiceField(ModelChoiceField):
    def __init__(self, *args, **kwargs):
        self.extra_allowed_values = kwargs.pop('extra_allowed_values', None)
        super(LazyModelChoiceField, self).__init__(*args, **kwargs)

    def _is_allowed_value(self, value):
        text_value = force_text(value)
        if self.extra_allowed_values and text_value in self.extra_allowed_values:
            return True
        else:
            return False

    def valid_value(self, value):
        if self._is_allowed_value(value):
            return True
        return super(LazyModelChoiceField, self).valid_value(value)

    def validate(self, value):
        """
        Validates that the input is in self.choices.
        """
        if self._is_allowed_value(value):
            return True
        super(LazyModelChoiceField, self).validate(value)

    def to_python(self, value):
        if self._is_allowed_value(value):
            return value
        return super(LazyModelChoiceField, self).to_python(value)


class CommaSeparatedIntegerField(LazyModelChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs['queryset'] = None
        super(CommaSeparatedIntegerField, self).__init__(*args, **kwargs)

    def _is_allowed_value(self, value):
        for val in value:
            try:
                int(val)
            except (TypeError, ValueError):
                return False
        return True


class SelectWithData(forms.Select):
    def render_option(self, selected_choices, option_value, option_label):
        option = self.objects.get(option_value)
        option_data = {
            'pk': option_value,
            'text': option_label,
        }
        if self.serializer and option:
            option_data.update(self.serializer(
                option, context={'request': self.request}).data)

        return u'<option value="{}" data-data=\'{}\'>{}</option>'.format(
            option_value, json.dumps(option_data), option_label)

    def render_options(self, *args, **kwargs):
        self.objects = {obj.id: obj for obj in self.choices.queryset}
        return super(SelectWithData, self).render_options(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        self.serializer = kwargs.pop('serializer', None)
        self.request = kwargs.pop('request', None)
        super(SelectWithData, self).__init__(*args, **kwargs)


if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^med_social\.fields\.ContentTypeRestrictedFileField"])
