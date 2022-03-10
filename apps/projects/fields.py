from collections import OrderedDict

from vendors.models import Vendor
from .models import StaffingRequest


def requests_as_choices():
    choices = OrderedDict()
    requests = StaffingRequest.objects.all().order_by('-id')
    for request in requests:
        choices[request.project] = choices.get(request.project, [])
        choices[request.project].append((request.id, request))
    return choices.items()


def vendors_as_choices():
    choices = OrderedDict()
    vendors = Vendor.objects.all().order_by('-avg_score')
    choices['Suggested vendors'] = []
    for vendor in vendors:
        choices['All vendors'] = choices.get('All vendors', [])
        choices['All vendors'].append((vendor.id, vendor))
    return choices.items()
