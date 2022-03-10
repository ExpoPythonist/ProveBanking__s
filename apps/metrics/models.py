import datetime
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import fields as generic


class MetricKindMixin(models.Model):
    RESPONSE_TIME = 1
    ACCEPTANCE_RATE = 2
    USER_RATING = 3

    METRIC_TYPE = (
        (RESPONSE_TIME, 'response',),
        (ACCEPTANCE_RATE, 'acceptance',),
        (USER_RATING, 'user_rating',),
    )

    kind = models.PositiveSmallIntegerField(choices=METRIC_TYPE)

    class Meta:
        abstract = True


class Metric(MetricKindMixin):

    SCORE_1 = 1
    SCORE_2 = 2
    SCORE_3 = 3
    SCORE_4 = 4
    SCORE_5 = 5
    SCORE_CHOICES = (
        (SCORE_1, '1',),
        (SCORE_2, '2',),
        (SCORE_3, '3',),
        (SCORE_4, '4',),
        (SCORE_5, '5',),
    )

    score = models.DecimalField(max_digits=2, decimal_places=1)
    created = models.DateTimeField(auto_now_add=True)

    #Object to which Metric score is calculated
    content_type = models.ForeignKey(ContentType, related_name='metric')
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    #Object to which Metric belongs
    target_type = models.ForeignKey(ContentType, related_name='metric_owned')
    target_id = models.PositiveIntegerField()
    target_object = generic.GenericForeignKey('target_type', 'target_id')

    @classmethod
    def get_response_score(self, time):
        if time <= datetime.timedelta(days=1):
            return Metric.SCORE_5
        elif time <= datetime.timedelta(days=2):
            return Metric.SCORE_4
        elif time <= datetime.timedelta(days=3):
            return Metric.SCORE_3
        elif time <= datetime.timedelta(days=4):
            return Metric.SCORE_2
        else:
            return Metric.SCORE_1

    @classmethod
    def get_acceptance_score(self, accepted):

        SCORE_ACCEPTED = 5
        SCORE_REJECTED = 0

        if accepted:
            return SCORE_ACCEPTED
        return SCORE_REJECTED


class MetricAggregate(MetricKindMixin):

    start_date = models.DateField()
    score = models.DecimalField(max_digits=2, decimal_places=1, null=True)

    #Object to which MetricAggregate belongs
    content_type = models.ForeignKey(ContentType,
                                     related_name='metric_aggregate')
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
