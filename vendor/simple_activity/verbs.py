class BaseVerb(object):
    code = '__base_verb__'
    template_name = 'activity/actions/base.html'

    def __eq__(self, other):
        direct_match = other == self.code
        attr_match = getattr(other, 'code', None) == self.code
        return direct_match or attr_match

    def render(self):
        raise NotImplementedError('Implement this in concrete class')
