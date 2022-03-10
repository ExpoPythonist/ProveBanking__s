from .models import ProposedResourceStatus as PRS


def get_status_options(current_user, resource, project):
    # if current user is vendor
    if current_user.is_vendor:
        if resource.vendor == current_user.vendor:
            return PRS.objects.filter(value=PRS.INITIATED)
        else:
            return None
    else:
        return PRS.objects.all()
    return None
