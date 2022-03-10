from django.contrib import admin
from .models import SLA, Response


@admin.register(SLA)
class SLAAdmin(admin.ModelAdmin):
    exclude = ('definitions',)

admin.site.register(Response)
