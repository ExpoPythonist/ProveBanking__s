from django.db import connection
from django.db.models.signals import (pre_delete,
                                      post_save,
                                      m2m_changed,)
from django.dispatch.dispatcher import receiver

from med_social.utils import get_current_tenant

from vendors.models import Vendor

from .models import (ProposedResource,
                     StaffingRequest,
                     RequestVendorRelationship,
                     Project,)
from .tasks import (new_resource,
                    status_change,
                    staffing_req,
                    sr_confirmation,
                    update_project_resource_dates,
                    update_staffing_dates,
                    staffing_req_client_email)


@receiver(pre_delete, sender=ProposedResource,
          dispatch_uid='projects.ProposedResource.pre_delete')
def pre_delete_proposed_resource(sender, **kwargs):
    instance = kwargs.get('instance')
    if instance.request:
        instance.request.update_status(commit=True)
    if instance.project:
        instance.project.update_status(commit=True)



@receiver(post_save, sender=RequestVendorRelationship,
          dispatch_uid='projects.RequestVendorRelationship.post_save')
def post_save_rv_relationship(sender, **kwargs):
    instance = kwargs.get('instance')
    created = kwargs.get('created')
    tenant = connection.get_tenant()
    answer_changed = instance.tracker.has_changed('answer')
    if answer_changed and instance.answer is not None:
        sr_confirmation.delay(tenant_id=tenant.id,
                              instance_id=instance.id,)

    if created:
        staffing_req.delay(tenant.id, instance.id)


@receiver(post_save, sender=Project,
          dispatch_uid='projects.Project.post_save')
def post_save_project(sender, **kwargs):
    instance = kwargs.get('instance')
    tenant = connection.get_tenant()
    start_changed = instance.tracker.has_changed('start_date')
    end_changed = instance.tracker.has_changed('end_date')
    if start_changed or end_changed:
        update_project_resource_dates.delay(tenant_id=tenant.id,
                                            project_id=instance.id)
