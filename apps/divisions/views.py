from django.http import JsonResponse

from .models import Division


def division_search(request):
    q = request.GET.get('q')
    if q:
        divs = Division.objects.filter(name__istartswith=q)[:10]
    else:
        divs = Division.objects.all()[:10]
    data = [{'value': str(div.id), 'label': div.name, 'id': div.id}
            for div in divs]
    return JsonResponse(data, safe=False)
