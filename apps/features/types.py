from med_social.utils import get_current_tenant


class Feature(int):
    def __new__(cls, *args, **kwargs):
        title = kwargs.pop('title')
        codename = kwargs.pop('codename')
        description = kwargs.pop('description')
        new = super(Feature, cls).__new__(cls, *args, **kwargs)
        new.title = title
        new.codename = codename
        new.description = description
        return new

    def get_title(self):
        return self.title

    def get_description(self):
        return self.description

    def is_enabled(self, tenant=None):
        tenant = tenant or get_current_tenant()
        return self in tenant.features

