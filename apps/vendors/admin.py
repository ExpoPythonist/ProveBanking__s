from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from import_export.admin import ExportMixin, ImportExportModelAdmin

from locations.models import Location
from .models import (Vendor, VendorLocation, VendorCategories, VendorRoles,
                     PortfolioItem, ProcurementContact, KindLabel, ClientReference, Invoice, ClientQueue,
                     CertVerification)
from .resources import VendorResource


class VendorAdmin(ExportMixin, admin.ModelAdmin):
    exclude = ('phone', 'story', 'founded', 'industries',
               'avg_score')
    resource_class = VendorResource
    list_display = ('name', 'website', 'slug', 'proven_score', 'potential_proven_score', 'client_score',
                    'potential_client_score', 'company_score', 'web_score', 'modified_on', 'sync_clearbit', )
    readonly_fields = ('slug', 'proven_score', 'potential_proven_score', 'client_score', 'potential_client_score', 'company_score', 'web_score', 'clearbit_data')
    search_fields = ('name', )


class VendorSearchTerm(Vendor):
    class Meta:
        proxy = True


class HasSearchKeyworkFilter(admin.SimpleListFilter):
    title = _('Search keywords?')
    parameter_name = 'has_search_keywords'

    def lookups(self, request, model_admin):
        return (
            ('with', 'with search keywords'),
            ('without', 'without search keywords'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'with':
            return queryset.exclude(search_keywords=[])
        elif value == 'without':
            return queryset.filter(search_keywords=[])
        return queryset



class VendorSearchTermAdmin(admin.ModelAdmin):
    list_filter = (HasSearchKeyworkFilter,)
    fields = ('name', 'search_keywords')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


class ProcurementAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super(ProcurementAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['locations'].queryset = Location.objects.filter(kind=Location.KIND_COUNTRY)
        return form


class ClientReferenceAdmin(admin.ModelAdmin):
    model = ClientReference
    list_display = ('id', 'vendor', 'client', 'email', 'weighted_value')
    readonly_fields = ('weighted_value',)


class InvoiceAdmin(admin.ModelAdmin):
    model = Invoice
    list_display = ('uuid', 'reference', 'date_verified')


class CertVerificationAdmin(admin.ModelAdmin):
    model = CertVerification


admin.site.register(Vendor, VendorAdmin)
admin.site.register(ProcurementContact, ProcurementAdmin)
admin.site.register(VendorLocation)
admin.site.register(VendorCategories)
admin.site.register(VendorRoles)
admin.site.register(PortfolioItem)
admin.site.register(KindLabel)
admin.site.register(VendorSearchTerm, VendorSearchTermAdmin)
admin.site.register(ClientReference, ClientReferenceAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(ClientQueue)
admin.site.register(CertVerification, CertVerificationAdmin)
