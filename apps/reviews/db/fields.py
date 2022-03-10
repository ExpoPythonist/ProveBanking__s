from django.db import models
from django.db.models import Avg
from django.contrib.contenttypes.fields import GenericRelation

from ..models import Metric


def __denorm_func__(self, commit=True):
    fields = []
    if self.__Reviews__average_field__:
        fields.append(self.__Reviews__average_field__)
        avg_score = self.reviews.aggregate(Avg('score'))['score__avg']
        if avg_score is not None:
            avg_score = float('{:.1f}'.format(avg_score))
        setattr(self, self.__Reviews__average_field__, avg_score)

    if self.__Reviews__count_field__:
        fields.append(self.__Reviews__count_field__)
        setattr(self, self.__Reviews__count_field__, self.reviews.count())

    if commit:
        self.save(update_fields=fields)


class ReviewsField(GenericRelation):
    def __init__(self, *args, **kwargs):
        self.average_field = kwargs.pop('average_field', 'avg_score')
        self.count_field = kwargs.pop('count_field', 'reviews_count')
        super(ReviewsField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(ReviewsField, self).contribute_to_class(cls, name)

        abstract = False
        attr_meta = getattr(cls, '_meta', None)
        if attr_meta:
            abstract = getattr(attr_meta, 'abstract', False) or getattr(attr_meta, 'proxy', False)
        if abstract:
            return

        Metric._supported_models.add(cls)

        setattr(cls, '__Reviews__average_field__', self.average_field)
        setattr(cls, '__Reviews__count_field__', self.count_field)
        setattr(cls, '__Reviews__denorm_reviews__',
                getattr(cls, '__Reviews__denorm_reviews__',
                        __denorm_func__))

        if self.average_field is not None:
            cls.add_to_class(self.average_field,
                    models.DecimalField(blank=True, null=True,
                                        max_digits=2, decimal_places=1))

        if self.count_field is not None:
            cls.add_to_class(self.count_field,
                    models.IntegerField(default=0, editable=False))

