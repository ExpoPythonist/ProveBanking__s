from django.contrib import admin
from django.db import IntegrityError

from vendors.models import (VendorServices, VendorCategories,
                            VendorIndustry, VendorRoles)

from .models import Category


class CategoryAdmin(admin.ModelAdmin):
    list_filter = ('kind', 'custom_kind')
    search_fields = ('name',)
    actions = ('merge', )

    class Meta:
        model = Category

    def merge(self, request, queryset):
        main = queryset[0]
        tail = queryset[1:]

        related = main._meta.get_all_related_objects()

        valnames = dict()
        for r in related:
            valnames.setdefault(r.model, []).append(r.field.name)

        for place in tail:
            if main.kind == place.kind:
                if main.kind == Category.KIND_SERVICE:
                    for vendor in place.vendors.all():
                        VendorServices.objects.get_or_create(service=main, vendor=vendor)
                    place.delete()

                if main.kind == Category.KIND_SKILL:
                    for vendor in place.vendors.all():
                        VendorCategories.objects.get_or_create(skill=main, vendor=vendor)
                    place.delete()

                if main.kind == Category.KIND_INDUSTRY:
                    for vendor in place.vendors.all():
                        VendorIndustry.objects.get_or_create(industry=main, vendor=vendor)
                    place.delete()
        
        self.message_user(request, "Merged into %s." % main)


admin.site.register(Category, CategoryAdmin)
