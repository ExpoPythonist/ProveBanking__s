from django.contrib.auth import get_user_model
from django.db.models import Q

from import_export import resources
from import_export import fields

from .models import Vendor, ProcurementContact


class VendorResource(resources.ModelResource):

    class Meta:
        model = Vendor
        fields = ('name', 'email', 'partner_since', 'joined_on',
                  'locations', 'summary', 'industries', 'categories',
                  'engage_process', 'kind', 'contacts', 'type',
                  'linkedin', 'twitter', 'website')

        export_order = ('name', 'summary', 'contacts', 'email',
                        'type', 'engage_process', 'locations',
                        'industries', 'categories', 'kind',
                        'website', 'linkedin', 'twitter',
                        'partner_since', 'joined_on')
        widgets = {
            'partner_since': {'format': '%d.%m.%Y'},
            'joined_on': {'format': '%d.%m.%Y'},
        }

    def __init__(self, *args, **kwargs):
        super(VendorResource, self).__init__(*args, **kwargs)
        self.fields['name'].column_name = 'Company name'
        self.fields['summary'].column_name = 'Summary'
        self.fields['contacts'].column_name = 'Supplier contacts'
        self.fields['email'].column_name = 'Supplier email'
        self.fields['type'].column_name = 'Procurement contacts'
        self.fields['engage_process'].column_name = 'Notes by procrement group'
        self.fields['locations'].column_name = 'Locations'
        self.fields['industries'].column_name = 'Industries'
        self.fields['categories'].column_name = 'Skills'
        self.fields['kind'].column_name = 'Status'
        self.fields['website'].column_name = 'Company website'
        self.fields['linkedin'].column_name = 'Linkedin'
        self.fields['twitter'].column_name = 'Twitter'
        self.fields['partner_since'].column_name = 'Partner since'
        self.fields['joined_on'].column_name = 'Joined Proven on'

    def dehydrate_locations(self, vendor):
        loc_list = list()
        for loc in vendor.locations.all():
            loc_list.append(loc.city)
        return ",".join(loc_list)

    def dehydrate_kind(self, vendor):
        return vendor.KIND_LABELS.get(vendor.kind)

    def dehydrate_categories(self, vendor):
        cat_list = list()
        for cat in vendor.categories.all():
            cat_list.append(cat.name)
        return ",".join(cat_list)

    def dehydrate_industries(self, vendor):
        cat_list = list()
        for cat in vendor.industries.all():
            cat_list.append(cat.name)
        return ",".join(cat_list)

    def dehydrate_contacts(self, vendor):
        user_list = list()
        for user in vendor.contacts.all():
            user_detail = user.get_name_display() + ' (' + user.email + ')'
            user_list.append(user_detail)
        u = get_user_model().objects.filter(email=vendor.email).first()
        if u:
            user_detail = u.get_name_display() + ' (' + u.email + ')'
            user_list.append(user_detail)
        return ",".join(user_list)

    def dehydrate_type(self, vendor):
        user_list = list()
        for obj in vendor.procurement_contacts.all():
            user_list.append("{}({})".format(obj.user.get_name_display(),
                             obj.user.email))

        if not user_list:
            q = Q(always_show=True)
            q = q | Q(categories=vendor.categories.values_list('id',
                                                               flat=True))
            contacts = ProcurementContact\
                .objects.filter(q).values_list('id', flat=True)

            # defualt procurement contacts
            contacts = contacts
            users = get_user_model().objects.filter(procurement_contacts__in=contacts)
            for user in users:
                user_list.append("{}({})".format(user.get_name_display(),
                                 user.email))
        return ",".join(user_list)
