from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from activity.models import Event


@login_required
def event_update(request, content_id, object_id, *args, **kwargs):
    content_id = content_id
    object_id = object_id
    Event.objects.filter(user=request.user,
                         content_type_id=content_id,
                         object_id=object_id).delete()
    return HttpResponse(status=200)
