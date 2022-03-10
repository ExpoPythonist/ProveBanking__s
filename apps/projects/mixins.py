from django.db import models
from django.db.models import Q

from model_utils.managers import QueryManager
from model_utils import Choices


class StatusModel(models.Model):
    DRAFT = 1
    STAFFING = 2
    STAFFED = 3

    STATUS = Choices(
        (DRAFT, 'draft', 'Draft',),
        (STAFFING, 'staffing', 'Staffing',),
        (STAFFED, 'staffed', 'Staffed',),
    )

    STATUS_CSS = {
        DRAFT: 'danger',
        STAFFING: 'warning',
        STAFFED: 'success',
    }

    STATUS_DESCRIPTIONS = {
        DRAFT: 'Draft projects are not visible to vendors',
        STAFFING: ('Staffing means you are actively looking for people for '
                   'this project'),
        STAFFED: ('Staffed means the project is fully staffed and vendors '
                  'should not longer propose people'),
    }

    status = models.PositiveSmallIntegerField(default=DRAFT, choices=STATUS)
    is_archived = models.BooleanField(default=False)

    objects = models.Manager()
    active = QueryManager(~Q(status=DRAFT) & ~Q(is_archived=True))
    drafts = QueryManager(status=DRAFT)
    staffing = QueryManager(status=STAFFING)
    staffed = QueryManager(status=STAFFED)
    archived = QueryManager(is_archived=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.id:
            self.update_status()
        return super(StatusModel, self).save(*args, **kwargs)

    def update_status(self):
        raise NotImplemented()

    def is_draft_status(self):
        return self.status == self.DRAFT

    def is_staffing_status(self):
        return self.status == self.STAFFING

    def is_staffed_status(self):
        return self.status == self.STAFFED

    def is_completed_status(self):
        return self.is_staffed()
        #return self.status == self.COMPLETED

    def is_confirmed_status(self):
        return self.status != self.UNCONFIRMED

    def get_status_css_class(self):
        return self.STATUS_CSS.get(self.status, 'default')

