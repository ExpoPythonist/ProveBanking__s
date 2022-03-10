from django.contrib import admin

from .models import Client


class ClientAdmin(admin.ModelAdmin):
    model = Client
    list_display = ('name', 'website', 'client_quality_score')
    fields = (
        'name', 'logo', 'website',
        'employee_count', 'registration_type', 'google_pagerank', 'alexa_rank', 'twitter_followers', 'market_cap',
        'annual_revenue', 'founded_date', 'client_quality_score', 'clearbit_data',
    )
    readonly_fields = ('client_quality_score', 'clearbit_data')


admin.site.register(Client, ClientAdmin)
