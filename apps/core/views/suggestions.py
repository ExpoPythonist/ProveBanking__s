from django.views.generic import View

from braces.views import JSONResponseMixin
from taggit.models import Tag

from med_social.decorators import member_required


class TagSuggestions(JSONResponseMixin, View):

    def get(self, request):
        q = self.request.GET.get('q', '').strip()
        tags = list(Tag.objects.filter(name__icontains=q).values('pk', 'name'))
        return self.render_json_response(tags)
tag_suggestions = member_required(TagSuggestions.as_view())
