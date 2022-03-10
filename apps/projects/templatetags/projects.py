from django import template
from django.db.models import Q, Sum

from med_social.utils import (today,
                              natural_date)

from ..models import (StaffingResponse, StaffingRequest, ProposedResource,
                      ProposedResourceStatus, Project)

register = template.Library()


@register.filter
def can_staff_resources(project, user):
    return True
    # Note: for now we want everyone to be able to do it.
    #return user.is_client and user.division_rels.filter(
    #    division=project.division, is_admin=True)


@register.assignment_tag
def get_proposed_resource_statuses():
    return ProposedResourceStatus.objects.all()


@register.assignment_tag
def get_request_colleagues(staffing_request, user):
    if user.is_vendor:
        return staffing_request.people.filter(
            Q(vendor=user.vendor) | Q(vendor=None))
    else:
        return staffing_request.people.all()


@register.simple_tag
def get_proposed_resource_status_count(staffing_request, status, user):
    qs = ProposedResource.objects.filter(request=staffing_request,
                                         status=status)
    if user.is_vendor:
        qs = qs.filter(resource__vendor=user.vendor)
    return qs.count()


@register.simple_tag
def get_budget_class(cost, budget):
    if all([cost, budget]):
        eighty = budget * 0.8
        if eighty <= cost <= budget:
            return 'warning'
        if cost > budget:
            return 'danger'
    return 'secondary'


@register.simple_tag
def get_remaining_budget_class(cost, budget):
    cost = cost or 0
    if budget:
        remaining = budget - cost
        if remaining <= 0:
            return 'danger'
    return 'secondary'


def get_spend_class(score):
    if score <= 2.5:
        return 'danger'
    if 2.5 < score < 4:
        return 'primary'
    if score > 4:
        return 'success'
register.simple_tag(get_spend_class)


def get_display_func(model, field):
    return getattr(model, 'get_{}_display'.format(field),
                   getattr(model, field))


def get_staffing_requests(project, user):
    if user.is_client:
        return project.staffing_requests.all()
    elif user.is_vendor:
        q = Q(is_public=True) | Q(vendors=user.vendor)
        return project.staffing_requests.filter(q)
register.assignment_tag(get_staffing_requests)


def get_open_staffing_requests(project, user):
    qs = project.staffing_requests.filter(status=StaffingRequest.STAFFING,
                                          is_archived=False)
    if user.is_vendor:
        q = Q(is_public=True) | Q(vendors=user.vendor)
        qs = qs.filter(q)
    return qs.distinct().count()
register.assignment_tag(get_open_staffing_requests)


def get_staffing_responses(request, user):
    if user.is_client:
        return request.responses.exclude(
            status=StaffingResponse.STATUS_DRAFT
        )
    elif user.is_vendor:
        return request.responses.filter(
            vendor=user.vendor,
        ).all()
register.assignment_tag(get_staffing_responses)


def get_proposed_staff_for_request(request, user):
    if user.is_client:
        proposed_resources = ProposedResource.objects.filter(
            request=request,
        ).order_by('-status__value')
    elif user.is_vendor:
        proposed_resources = ProposedResource.objects.filter(
            request=request,
            resource__vendor=user.vendor,
        ).order_by('-status__value')

    for proposed_resource in proposed_resources:
        proposed_resource.past_projects = proposed_resource.resource.proposed.filter(
            status__value=ProposedResourceStatus.SUCCESS).distinct().count()
    return proposed_resources

register.assignment_tag(get_proposed_staff_for_request)


def get_total_earned_by_vendor_on_project(project, vendor):
    cost = 0
    # Cost from Deliverables
    cost += StaffingResponse.objects.filter(
        vendor=vendor,
        request__project=project,
        request__kind=StaffingRequest.KIND_FIXED,
        is_accepted=True
    ).aggregate(Sum('rate'))['rate__sum'] or 0

    # Cost from staff
    cost += project.proposals.filter(
        status__value=ProposedResourceStatus.SUCCESS,
        resource__vendor=vendor
    ).aggregate(Sum('final_rate'))['final_rate__sum'] or 0
    return int(cost)
register.assignment_tag(get_total_earned_by_vendor_on_project)


@register.filter
def get_staffed_count_for_vendor(project, vendor):
    return project.proposals.filter(
        resource__vendor=vendor,
        status=ProposedResourceStatus.SUCCESS).count()


@register.filter
def render_response_field(response, field_name):
    tmpl = template.loader.get_template('responses/response_field.html')
    ctx = template.Context({
        'value': get_display_func(response, field_name)
    })
    if response.is_contradicting_field(field_name):
        ctx['is_contradicting'] = True
        ctx['original_value'] = get_display_func(response.request, field_name)
    return tmpl.render(ctx)


@register.filter
def render_status(project, kind):
    tmpl = template.loader.get_template(
        'projects/status/{0}/{1}.html'.format(
            project.get_status_display().lower(), kind))
    return tmpl.render(template.Context({'project': project}))


@register.filter
def render_response_status(response, kind):
    status = response.get_status_display().lower()
    if response.request.is_fixed_price and response.accepted:
        status = 'accepted'
    tmpl = template.loader.get_template(
        'responses/status/{0}/{1}.html'.format(
            status,
            kind
        )
    )
    return tmpl.render(template.Context({'response': response}))


@register.assignment_tag
def has_vendor_responded(request, vendor):
    responses = request.responses.filter(
        vendor_id=vendor.id
    )
    if responses.count():
        return True
    else:
        return False


@register.filter
def can_use_proposed_status(status, user):
    return status.is_allowed_to_use(user)


ICON_MAP = {
    'location': 'map-marker',
    'allocation': 'dashboard',
    'role': 'sitemap',
    'dates': 'calendar',
    'skill_level': 'sliders',
}

FIELD_RENDERERS = {
    'allocation': lambda l: '{}%'.format(l),
    'dates': lambda (s, e): '{} <span class="text-muted">to</span> {}'.format(
        natural_date(s), natural_date(e))
}


def _render_field(field_name, value):
    return FIELD_RENDERERS.get(field_name, lambda v: v)(value)


def _to_display(name):
    return name.replace('_', ' ').capitalize()


@register.assignment_tag
def get_missing_skills(proposed):
    if not proposed.request:
        return []
    request = proposed.request
    required_skills = request.categories.all()
    present_skills = proposed.resource.categories.filter(
        id__in=[r.id for r in required_skills])
    return set(required_skills) - set(present_skills)


@register.assignment_tag
def get_fields_with_conflicts(proposed):
    conflicts = []
    fields = ['location', 'role', 'skill_level', 'allocation']
    if not proposed.request:
        return []

    request = proposed.request
    for field in fields:
        value = getattr(proposed, field)
        expected = getattr(request, field) or 'Not specified'
        if value == expected:
            continue
        f_dict = {
            'name': field,
            'display': _to_display(field),
            'icon': ICON_MAP[field],
            'value': _render_field(field, value),
            'expected': _render_field(field, expected)
        }
        if expected and (value != expected):
            f_dict['conflicts'] = True
        conflicts.append(f_dict)

    dates_value = (proposed.start_date, proposed.end_date)
    dates_expected = (request.start_date, request.end_date)
    if dates_expected and (dates_value != dates_expected):
        f_dict = {
            'name': 'dates',
            'display': _to_display('dates'),
            'icon': ICON_MAP['dates'],
            'value': _render_field('dates', dates_value),
            'expected': _render_field('dates', dates_expected),
            'conflicts': True
        }
        conflicts.append(f_dict)
    return conflicts


@register.assignment_tag
def get_possible_forward_statuses(resource, user):
    if resource.status:
        return resource.status.get_possible_forward_statuses(user, resource)
    else:
        return ProposedResourceStatus.objects.filter(
            value=ProposedResourceStatus.INITIATED)


@register.assignment_tag
def get_remaining_budget(cost, budget):
    cost = cost or 0
    if budget:
        return budget - cost


@register.filter(name='get_class')
def get_class(value):
    return value.__class__.__name__


@register.assignment_tag
def get_ongoing_projects(user):
    projects = Project.objects.filter(status=Project.STAFFING)
    if user.is_vendor:
        q = Q(staffing_requests__vendors=user.vendor.id)
        q = q | Q(staffing_requests__is_public=True)
        projects = projects.filter(q).exclude(is_archived=True)
    else:
        projects = projects.filter(owners=user).exclude(is_archived=True)
    return projects.count()
