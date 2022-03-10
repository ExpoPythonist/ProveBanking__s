class KindMixin(object):
    KIND_PREFERRED = 1
    KIND_APPROVED = 2
    KIND_PROSPECTIVE = 3
    KIND_CHOICES = (
        (KIND_PREFERRED, 'preferred'),
        (KIND_APPROVED, 'approved'),
        (KIND_PROSPECTIVE, 'prospective'),
    )

    KIND_CHOICES_DICT = dict(KIND_CHOICES)

    KIND_LABELS = {
        KIND_PREFERRED: 'Preferred',
        KIND_APPROVED: 'Approved',
        #KIND_PROSPECTIVE: 'Prospective',
    }
    KIND_CSS_CLASSES = {
        KIND_PREFERRED: 'success',
        KIND_APPROVED: 'warning',
        KIND_PROSPECTIVE: 'secondary',
    }

    KIND_SCORES = {
        KIND_PREFERRED: 200,
        KIND_APPROVED: 20,
        KIND_PROSPECTIVE: 0,
    }

    KIND_DESC = {
        KIND_PREFERRED: 'Fast contracting and pre-negotiated rates',
        KIND_APPROVED: 'Contracting and negotiation may take extra '
                       'time for non-preferred',
        KIND_PROSPECTIVE: 'Have not worked with our firm yet - will '
                          'involve a potentially lengthy approval and '
                          'contracting process',
    }

    @property
    def kind_choices(self):
        from .models import KindLabel
        return KindLabel.objects.values_list('kind', 'label')

    @property
    def kind_filter_choices(self):
        from .models import KindLabel
        return KindLabel.objects.filter(filter_default=True).values_list('kind')

    @property
    def kind_labels(self):
        from .models import KindLabel
        return dict(KindLabel.objects.values_list('kind', 'label'))

    @property
    def kind_labels_diplayable(self):
        from .models import KindLabel
        return dict(KindLabel.objects.filter(show_label=True).values_list('kind', 'label'))

    # @property
    # def KIND_DESC(self):
    #     return dict(KindLabel.objects.values_list('kind', 'description'))
