from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from annoying.functions import get_object_or_None
from django_atomic_celery import task
from notifications.signals import notify
from tenant_schemas.utils import tenant_context, get_tenant_model

from activity.tasks import event_generator
from customers.models import Customer
from vendors.models import Vendor
from metrics.models import Metric
from users.models import UserDivisionRel
from .models import (ProposedResource,
                     StaffingRequest,
                     StatusFlow,
                     RequestVendorRelationship,
                     ProposedResourceStatus, Project)
from .emails.views import (NewResourceEmail,
                           ResourceStatusChangeEmail,
                           NewStaffingEmail,
                           RequestInfoEmail,
                           StaffingConfirmationView,
                           ShareProjectEmail,
                           NewStaffingClientEmail,
                           )


@task
def new_resource(tenant_id, pr_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        proposed_resource = get_object_or_None(ProposedResource, id=pr_id)

        if not proposed_resource:
            return

        resource = proposed_resource.resource
        sender = proposed_resource.created_by
        if proposed_resource.request:

            recipients = list(proposed_resource.request.owners.all() or
                              proposed_resource.request.project.owners.all())
        else:
            recipients = list(proposed_resource.project.owners.all())

        if resource.is_vendor:
            vendor = get_object_or_None(get_user_model(),
                                        email=resource.vendor.email)
            recipients.append(vendor)

        if resource.has_joined:
            recipients.append(resource)

        recipients = set(recipients)

        if sender in recipients:
            recipients.remove(sender)

        recipient_list = [recipient.id for recipient in recipients]
        content_id = ContentType.objects.get_for_model(ProposedResource).id
        event_generator.delay(tenant_id=tenant_id,
                              user_list=recipient_list,
                              object_id=proposed_resource.id,
                              content_id=content_id
                              )

        for recipient in recipients:

            notify.send(
                sender=sender,
                verb='added a new candidate {candidate}'.format(candidate=resource.get_name_display()),
                target=None,
                action_object=proposed_resource,
                recipient=recipient
            )

            NewResourceEmail(user=sender,
                             recipient=recipient,
                             proposed_resource=proposed_resource).send()


@task
def status_change(tenant_id, pr_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        proposed_resource = get_object_or_None(ProposedResource, id=pr_id)

        if not proposed_resource:
            return

        resource = proposed_resource.resource
        sender = proposed_resource.changed_by

        if proposed_resource.request:
            recipients = list(proposed_resource.request.owners.all() or
                              proposed_resource.request.project.owners.all())
        else:
            recipients = list(proposed_resource.project.owners.all())

        forward_client = [value.forward for value in
                          proposed_resource.status.forward_flows.
                          filter(Q(driver=StatusFlow.DRIVER_ALL) |
                                 Q(driver=StatusFlow.DRIVER_CLIENT))]

        forward_vendor = [value.forward for value in
                          proposed_resource.status.forward_flows.
                          filter(Q(driver=StatusFlow.DRIVER_ALL) |
                                 Q(driver=StatusFlow.DRIVER_VENDOR))]

        if resource.is_vendor:
            vendor = get_object_or_None(get_user_model(),
                                        email=resource.vendor.email)
            recipients.append(vendor)

        if resource.has_joined:
            recipients.append(resource)

        recipients = set(recipients)

        if sender in recipients:
            recipients.remove(sender)

        recipient_list = [recipient.id for recipient in recipients]
        content_id = ContentType.objects.get_for_model(ProposedResource).id
        event_generator.delay(tenant_id=tenant_id,
                              user_list=recipient_list,
                              object_id=proposed_resource.id,
                              content_id=content_id
                              )

        for recipient in recipients:
            if recipient.is_vendor:
                forwards = forward_vendor
            else:
                forwards = forward_client

            notify.send(
                sender=sender,
                verb='changed status of {candidate} to {status}'
                .format(candidate=resource.get_name_display(),
                        status=proposed_resource.status),
                target=None,
                action_object=proposed_resource,
                recipient=recipient
            )

            ResourceStatusChangeEmail(user=sender,
                                      recipient=recipient,
                                      forwards=forwards,
                                      proposed_resource=proposed_resource)\
                .send()


@task
def staffing_req(tenant_id, instance_id):
    tenant = get_object_or_None(Customer, id=tenant_id)

    if not tenant:
        return
    with tenant_context(tenant):
        relation_obj = get_object_or_None(RequestVendorRelationship,
                                          id=instance_id)
        if not relation_obj:
            return

        sender = relation_obj.created_by
        recipient_list = []
        staffing_request = relation_obj.request
        vendor = relation_obj.vendor
        recipient = get_object_or_None(get_user_model(), email=vendor.email)
        if recipient:
            recipient_list.append(recipient.id)
            data = dict(sender=sender,
                        action_object=staffing_request,
                        recipient=recipient,
                        verb='invited you to fulfill {staffing_req}'
                        .format(staffing_req=staffing_request))
            notify.send(**data)

            NewStaffingEmail(user=sender,
                             recipient=recipient,
                             staffing_request=staffing_request,
                             ).send()

        content_id = ContentType.objects.get_for_model(StaffingRequest).id
        event_generator.delay(tenant_id=tenant_id,
                              user_list=recipient_list,
                              object_id=staffing_request.id,
                              content_id=content_id
                              )


@task
def request_info_task(tenant_id, user_list, message, sender_id, sr_id):

    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        staffing_request = get_object_or_None(StaffingRequest,
                                              id=sr_id)
        if not staffing_request:
            return

        sender = get_object_or_None(get_user_model(), id=sender_id)
        if not sender:
            return
        users = get_user_model().objects.filter(id__in=user_list)

        for user in users:
            RequestInfoEmail(user=user, sender=sender,
                             message=message,
                             staffing_request=staffing_request).send()


@task
def sr_confirmation(tenant_id, instance_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        try:
            relation_object = get_object_or_None(RequestVendorRelationship,
                                                 id=instance_id)
        except ObjectDoesNotExist:
            return
        user = relation_object.created_by
        vendor = relation_object.vendor
        staffing_request = relation_object.request
        recipients = (staffing_request.owners.all() or
                      staffing_request.project.owners.all())

        if relation_object.answer == RequestVendorRelationship.accepted:
            for recipient in recipients:
                data = dict(sender=vendor,
                            action_object=staffing_request,
                            recipient=recipient,
                            verb='accepted to fulfill {staffing_req}'
                            .format(staffing_req=staffing_request))

                notify.send(**data)
                StaffingConfirmationView(user=user,
                                         vendor=vendor,
                                         recipient=recipient,
                                         staffing_request=staffing_request,
                                         confirm=True,).send()

        elif (relation_object.answer == RequestVendorRelationship.rejected
                and user.email != vendor.email):
            for recipient in recipients:
                data = dict(sender=vendor,
                            action_object=staffing_request,
                            recipient=recipient,
                            verb='rejected to fulfill {staffing_req}'
                            .format(staffing_req=staffing_request))
                notify.send(**data)
                StaffingConfirmationView(user=user,
                                         vendor=vendor,
                                         recipient=recipient,
                                         staffing_request=staffing_request,
                                         confirm=False,).send()


@task
def staffing_req_user_add(tenant_id, stfrq_pk, user_list, req_user_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):

        request = get_object_or_None(StaffingRequest, pk=stfrq_pk)
        if not request:
            return
        req_user = get_object_or_None(get_user_model(), pk=req_user_id)
        if not req_user:
            return

        user_list = get_user_model().objects.filter(id__in=user_list)
        status = get_object_or_None(ProposedResourceStatus,
                                    value=ProposedResourceStatus.INITIATED)

        for user in user_list:
            ProposedResource\
                .objects.get_or_create(resource=user,
                                       project=request.project,
                                       request=request,
                                       defaults=
                                       {'changed_by': req_user,
                                        'created_by': req_user,
                                        'status': status,
                                        'role': request.role,
                                        'end_date': request.end_date,
                                        'start_date': request.start_date}
                                       )


@task
def create_request_vendor_relation(tenant_id, stfrq_pk,
                                   vendorpk_list, req_user_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):

        request = get_object_or_None(StaffingRequest, pk=stfrq_pk)
        if not request:
            return
        req_user = get_object_or_None(get_user_model(), pk=req_user_id)
        if not req_user:
            return

        vendor_list = Vendor.objects.filter(id__in=vendorpk_list)

        for vendor in vendor_list:
            RequestVendorRelationship\
                .objects.get_or_create(vendor=vendor,
                                       request=request,
                                       defaults={
                                           'created_by': req_user,
                                       })


@task
def share_project_mail(tenant_id, project_pk,
                       user_id, message, recipient_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        project = get_object_or_None(Project, pk=project_pk)
        if not project:
            return
        user = get_object_or_None(get_user_model(), pk=user_id)
        recipient = get_object_or_None(get_user_model(), pk=recipient_id)
        if not user or not recipient:
            return
        if user != recipient:
            data = dict(sender=user,
                        action_object=project,
                        recipient=recipient,
                        verb='shared a project {project}'
                        .format(project=project))
            notify.send(**data)
            ShareProjectEmail(user=user,
                              recipient=recipient,
                              project=project,
                              message=message).send()


@task
def req_vendor_response_metric(tenant_id):
    from metrics.tasks import create_metric
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        objects = RequestVendorRelationship.objects\
            .filter(metric=None)
        content_type = ContentType\
            .objects.get_for_model(RequestVendorRelationship)
        target_type = ContentType\
            .objects.get_for_model(Vendor)
        for obj in objects:
            time = obj.get_response_time()
            if time:
                score = Metric.get_response_score(time)
                create_metric.delay(tenant_id=tenant.id,
                                    content_type=content_type.id,
                                    object_id=obj.id,
                                    target_type=target_type.id,
                                    target_id=obj.vendor.id,
                                    kind=Metric.RESPONSE_TIME,
                                    score=score)


@task
def proposed_acceptance_metric(tenant_id):
    from metrics.tasks import create_metric
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        q = Q(request__status=StaffingRequest.STAFFED)
        q = q | Q(project__status=Project.STAFFED)
        q = q | Q(status=ProposedResourceStatus.SUCCESS)

        objects = ProposedResource.objects.filter(metric=None).filter(q)\
            .exclude(resource__vendor=None)

        content_type = ContentType\
            .objects.get_for_model(ProposedResource)

        target_type = ContentType\
            .objects.get_for_model(Vendor)
        for obj in objects:
            score = Metric.get_acceptance_score(obj.is_accepted())
            create_metric.delay(tenant_id=tenant.id,
                                content_type=content_type.id,
                                object_id=obj.id,
                                target_type=target_type.id,
                                target_id=obj.resource.vendor.id,
                                kind=Metric.ACCEPTANCE_RATE,
                                score=score)


@task
def proposed_resource_dates(tenant_id, project_id, proposed_id):
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        project = get_object_or_None(Project, id=project_id)
        proposed = get_object_or_None(ProposedResource, id=proposed_id)

        if not project and proposed:
            return
        proposed.start_date = project.start_date
        proposed.end_date = project.end_date
        proposed.save()


@task
def proposed_staffing_dates(tenant_id, staffing_id, proposed_id):
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        request = get_object_or_None(StaffingRequest, id=staffing_id)
        proposed = get_object_or_None(ProposedResource, id=proposed_id)

        if not request and proposed:
            return
        proposed.start_date = request.start_date
        proposed.end_date = request.end_date
        proposed.save()


@task
def update_project_resource_dates(tenant_id, project_id):
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        project = get_object_or_None(Project, id=project_id)
        if not project:
            return
        for proposed in project.proposals.all():
            proposed_resource_dates.delay(tenant_id=tenant.id,
                                          project_id=project.id,
                                          proposed_id=proposed.id)


@task
def update_staffing_dates(tenant_id, staffing_id):
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        request = get_object_or_None(StaffingRequest, id=staffing_id)
        if not request:
            return

        for proposed in request.proposed.all():
            proposed_staffing_dates.delay(tenant_id=tenant.id,
                                          staffing_id=request.id,
                                          proposed_id=proposed.id)


@task
def staffing_req_client_email(tenant_id, instance_id):
    tenant = get_object_or_None(Customer, id=tenant_id)

    if not tenant:
        return
    with tenant_context(tenant):
        staffing_request = get_object_or_None(StaffingRequest,
                                              id=instance_id)
        if not staffing_request:
            return

        sender = staffing_request.created_by

        recipient_list = []
        if staffing_request.project.division:
            recipient_list = [obj.user for obj in UserDivisionRel.objects
                              .filter(division=staffing_request.project.division,
                                      is_admin=True)]

        if sender in recipient_list:
            recipient_list.remove(sender)

        for recipient in recipient_list:
            data = dict(sender=sender,
                        action_object=staffing_request,
                        recipient=recipient,
                        verb='created new staffing request {staffing_req}'
                        .format(staffing_req=staffing_request))
            notify.send(**data)

            NewStaffingClientEmail(user=sender,
                                   recipient=recipient,
                                   staffing_request=staffing_request,
                                   ).send()
