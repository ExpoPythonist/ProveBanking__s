from django.forms.widgets import (DateInput, Textarea, Select, SelectMultiple,
                                  URLInput, TextInput, FileInput, NumberInput)
from django.forms import CharField as FormCharField
from django.forms import DateField as FormDateField, DecimalField
from django.forms import Field as BaseFormField
from django.forms.models import ModelMultipleChoiceField
from django.views.generic.base import View
from django.http.response import Http404
from django.db.models.signals import class_prepared
from django.db.models import PositiveSmallIntegerField, CharField, ForeignKey


__all__ = ('apply',)

# Monkey patch django and other libraries to modify defaults if they are going
# to be user sitewide.
#
# Note: Try to subclass things and modify behaviour first and only monkey patch
# as a last resort. For example, adding 'date-widget' attribute to datefield
# requires modifying every form we use so we can patch for that. Also, it
# doesn't modify default documented behaviour of django.

def model_multiple_choice_init(self, *args, **kwargs):
    ModelMultipleChoiceField.__orig_init__(self, *args, **kwargs)
    self.help_text = kwargs.get('help_text', ' ')

def set_required(self, value):
    value = bool(value)
    self.required = value
    if self.widget:
        self.widget.is_required = value
        self.widget.attrs['selectize-allow-empty-option'] = 'yes'


def build_date_attrs(self, *args, **kwargs):
    attrs = super(DateInput, self).build_attrs(*args, **kwargs)
    attrs['data-widget'] = 'datepicker'
    attrs['class'] = attrs.get('class', ' ').replace('text-field', '')
    return attrs


def build_textarea_attrs(self, *args, **kwargs):
    attrs = super(Textarea, self).build_attrs(*args, **kwargs)
    attrs['rows'] = attrs.get('force_rows', 2)
    attrs['autoresize'] = attrs.get('autoresize', 'true')
    placeholder = attrs.get('placeholder', '').strip()

    if not self.is_required and 'data-skip' not in attrs:
        if placeholder:
            placeholder = "%s (optional)" % placeholder
        else:
            placeholder = 'Optional'

    attrs['placeholder'] = placeholder
    return attrs


def build_select_attrs(self, *args, **kwargs):
    attrs = super(Select, self).build_attrs(*args, **kwargs)
    attrs['data-selectize'] = attrs.get('data-selectize', 'yes')
    if not attrs.get('selectize-placeholder') and 'data-skip' not in attrs:
        if attrs.get('selectize-create', False):
            attrs['selectize-placeholder'] = 'Type to search or add a new one'
        else:
            attrs['selectize-placeholder'] = 'Type to search'
        if not self.is_required:
            attrs['selectize-placeholder'] += ' (optional)'
    if not attrs.get('placeholder') and 'data-skip' not in attrs:
        attrs['placeholder'] = 'Tap to select'
        if not self.is_required:
            attrs['placeholder'] += ' (optional)'
    return attrs


def build_textinput_attrs(self, *args, **kwargs):
    attrs = super(TextInput, self).build_attrs(*args, **kwargs)
    placeholder = attrs.get('placeholder', '').strip()

    if not self.is_required:
        if placeholder:
            placeholder = "%s (optional)" % placeholder
        else:
            placeholder = 'Optional'

    attrs['placeholder'] = placeholder
    attrs['class'] = attrs.get('class', ' ') + ' text-field'
    return attrs


def build_numberinput_attrs(self, *args, **kwargs):
    attrs = super(NumberInput, self).build_attrs(*args, **kwargs)
    attrs['type'] = 'text'
    return attrs


def build_selectmultiple_attrs(self, *args, **kwargs):
    attrs = super(SelectMultiple, self).build_attrs(*args, **kwargs)
    attrs['data-selectize'] = attrs.get('data-selectize', 'yes')
    # attrs['ignore-enhance-mobile'] = 'yes'
    return attrs


def build_urlinput_attrs(self, *args, **kwargs):
    attrs = super(URLInput, self).build_attrs(*args, **kwargs)
    # attrs['novalidate'] = ''
    return attrs


def build_fileinput_attrs(self, *args, **kwargs):
    attrs = super(FileInput, self).build_attrs(*args, **kwargs)
    attrs['class'] = attrs.get('class', '') + ' filestyle'
    return attrs


def custom_dispatch(self, *args, **kwargs):
    # Check for feature enabled/purchased
    # TODO
    features = set(getattr(self, 'features_required', []))
    current_tenant = self.request.tenant
    missing_features = features - set(current_tenant.features)
    if current_tenant and missing_features:
        raise Http404()
    return self.__orig_dispatch__(*args, **kwargs)


def text_strip_clean(self, value, *args, **kwargs):
    """Strip textareas and textinputs clean of any spaces and other unprintable
    characters"""

    skip_widgets = ['password', 'hidden']
    if hasattr(self, 'widget'):
        if (hasattr(self.widget, 'input_type')
            and self.widget.input_type in skip_widgets):
            return super(FormCharField, self).clean(value, *args, **kwargs)

    value = self.to_python(value)
    if isinstance(value, basestring):
        value = value.strip()
    return super(FormCharField, self).clean(value, *args, **kwargs)


def init_date_widget(self, attrs=None, format=None):
    super(DateInput, self).__init__(attrs)
    self.format = '%d %B, %Y'
    self.manual_format = True


def init_date_field(self, *args, **kwargs):
    super(FormDateField, self).__init__(*args, **kwargs)
    # FIXME: I am a bad hack
    self.input_formats = ['%d %B, %Y', '%d %b, %Y'] + list(self.input_formats)

def decimal_to_python(self, value):
    _value = str(value).replace(',', '')
    return self._old_to_python(_value)

def apply():
    ModelMultipleChoiceField.__orig_init__ = ModelMultipleChoiceField.__init__
    ModelMultipleChoiceField.__init__ = model_multiple_choice_init
    FormCharField.clean = text_strip_clean
    FormDateField.__init__ = init_date_field
    DateInput.__init__ = init_date_widget
    DecimalField._old_to_python = DecimalField.to_python
    DecimalField.to_python = decimal_to_python
    DateInput.build_attrs = build_date_attrs
    Textarea.build_attrs = build_textarea_attrs
    Select.build_attrs = build_select_attrs
    SelectMultiple.build_attrs = build_selectmultiple_attrs
    URLInput.build_attrs = build_urlinput_attrs
    TextInput.build_attrs = build_textinput_attrs
    NumberInput.build_attrs = build_numberinput_attrs
    BaseFormField.set_required = set_required
    View.__orig_dispatch__ = View.dispatch
    View.dispatch = custom_dispatch


def extend_django_model(sender, **kwargs):
    """
    Add a kind small positive integer field to Group model.
    """
    if sender.__name__ == "Group":
        fields = [F.name for F in sender._meta.fields]
        if 'kind' in fields:
            return

        Group = sender
        Group.DEFAULT_USER = 1
        Group.DEFAULT_ADMIN = 2

        Group.PERMISSIONS = (
            ('admin', 'Admin rights', None, True),
        )

        kind = PositiveSmallIntegerField('kind', default=None, null=True,
                                         blank=True)
        kind.contribute_to_class(sender, "kind")

        vendor = ForeignKey('vendors.Vendor', null=True, blank=True,
                            related_name='groups')
        vendor.contribute_to_class(sender, 'vendor')

        display_name = CharField('Role Name', max_length=67, default='',
                                 null=True)
        display_name.contribute_to_class(sender, "display_name")

        Group._meta.unique_together += (('vendor', 'kind',),)

    if sender.__name__ == "Permission":
        fields = [F.name for F in sender._meta.fields]
        if 'visibility' in fields:
            return

        Permission = sender
        Permission.CLIENT = 1
        Permission.VENDOR = 2
        Permission.ALL = 3
        Permission.VISIBILITY_CHOICES = (
            (Permission.CLIENT, 'Client'),
            (Permission.VENDOR, 'Vendor'),
            (Permission.ALL, 'All'),
        )
        field = PositiveSmallIntegerField("visibility", null=True, blank=True,
                            choices=Permission.VISIBILITY_CHOICES)
        field.contribute_to_class(sender, "visibility")

class_prepared.connect(extend_django_model)
