from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from .models import Customer


def community_view(request, slug):
    if request.user.is_authenticated():
        community = get_object_or_404(Customer, domain_url=slug + '.proven.cc')
    else:
        community = get_object_or_404(Customer, is_public_instance=True, domain_url=slug + '.proven.cc')
    return render(request, 'community_view.html', {'community': community})
