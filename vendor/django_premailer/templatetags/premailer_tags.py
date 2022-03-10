from django import template

from premailer import transform

register = template.Library()


@register.tag
def premailer(parser, token):
    nodelist = parser.parse(('endpremailer',))
    parser.delete_first_token()
    args = token.split_contents()[1:]
    return PremailerNode(nodelist,
                         [parser.compile_filter(arg) for arg in args])


class PremailerNode(template.Node):
    def __init__(self, nodelist, filter_expressions):
        self.nodelist = nodelist
        self.filter_expressions = filter_expressions

    def render(self, context):
        rendered = self.nodelist.render(context)
        base_url = self.filter_expressions[0].resolve(context)
        return transform(rendered, base_url=base_url)
