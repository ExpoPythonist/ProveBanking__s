from watson import search as watson
from .models import Project, StaffingRequest

if not watson.is_registered(StaffingRequest):
    watson.register(StaffingRequest.objects.all(),
                    fields=("id", "title", "role", "description", "project",))

if not watson.is_registered(Project):
    watson.register(Project.objects.all(),
                    fields=("title", "staffing_requests__title",
                            "staffing_requests__role", "user",
                            "staffing_requests__proposed__resource",))
