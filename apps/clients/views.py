import json
import math
import urllib2
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from med_social.decorators import member_required
from vendors.filters import VendorFilter
from vendors.models import Vendor
from vendors.utils import retrieve_clearbit_data


def client_search(request):
    q = request.GET.get('q')
    if q:
        response = urllib2.urlopen('https://autocomplete.clearbit.com/v1/companies/suggest?query=' + q)
        resp_data = json.load(response)

        if resp_data:
            data = [{
                'pk': 'http://' + client.get('domain', '') + ' ' + (client.get('name', '') or ''),
                'text': client.get('name'),
                'caption': client.get('domain'),
                'logo': client.get('logo'),
                'domain': client.get('domain', ''),
                'clearbit': True,
            } for client in resp_data]
        else:
            data = []
    else:
        data = []
    return JsonResponse(data, safe=False)


def client_search_combined(request):
    q = request.GET.get('q')
    data = []

    filtered_vendors = VendorFilter(
        request.GET,
        request=request,
        queryset=Vendor.objects.all()
    )

    default_logo = settings.STATIC_URL + 'images/defaults/placeholder-co.png'
    vendor_data = [{
        'value': client.id,
        'label': client.name,
        'registered': "fa fa-check-square text-success",
        'website': client.website,
        'domain': client.domain,
        'logo': client.logo.url if client.logo else default_logo
    } for client in list(filtered_vendors)]

    if q:
        response = urllib2.urlopen('https://autocomplete.clearbit.com/v1/companies/suggest?query=' + q)
        resp_data = json.load(response)

        if resp_data:
            data = [{
                'value': client.get('name'),
                'label': client.get('name'),
                'caption': client.get('domain'),
                'domain': client.get('domain', ''),
                'logo': client.get('logo'),
                'website': 'http://' + client.get('domain'),
                'clearbit': True,
            } for client in resp_data]

        vendor_data.extend(data)
    return JsonResponse(vendor_data, safe=False)


@member_required
def score_estimate(request, slug):
    vendor = get_object_or_404(Vendor, slug=slug)
    base = int(vendor.proven_score)

    domain = request.GET.get('domain')
    if domain:
        data = retrieve_clearbit_data(domain)
        if data and 'metrics' in data and 'alexaGlobalRank' in data['metrics']:
            score = int(math.tanh(1.0/math.log(data['metrics']['alexaGlobalRank'] + 1) * math.pi) * 5)
            return JsonResponse({'old': base, 'new': base + score}, safe=False)
    return JsonResponse({'old': base, 'new': base}, safe=False)
