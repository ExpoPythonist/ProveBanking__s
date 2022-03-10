from simple_activity.managers import register_method


@register_method(name='for_clients')
def for_clients(self):
    return self.exclude(visibility=self.model.VENDORS)


@register_method(name='for_vendors')
def for_vendors(self):
    return self.exclude(visibility=self.model.CLIENTS)
