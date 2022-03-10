from collections import OrderedDict


class FieldsetMixin(object):
    fieldsets = tuple()

    def __init__(self, *args, **kwargs):
        self.__setup_fieldsets__()

    def __setup_fieldsets__(self):
        # TODO: write description
        fieldsets = OrderedDict()
        fieldset_maps = {}
        rows_map = {}

        for fieldset in self.fieldsets:
            set_label, fields = fieldset
            fieldsets[set_label] = []
            for field in fieldset[1].get('fields', []):
                fieldset_maps[field] = set_label
            rows = []
            for row in fieldset[1].get('rows', []):
                field_row = []
                for field in row:
                    field_row.append(self[field])
                rows.append(field_row)
            rows_map[set_label] = rows

        for field in self:
            set_label = fieldset_maps.get(field.name)
            if set_label:
                fieldsets[set_label].append(field)
        self.fieldsets = []

        for fieldset, fields in fieldsets.items():
            self.fieldsets.append((fieldset, {
                'fields': fields,
                'rows': rows_map.get(fieldset, [])
            }))

