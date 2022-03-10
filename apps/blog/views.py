from django.views.generic import ListView
from django.http import Http404

from .models import Blog

class BlogList(ListView):
    template_name = 'blog/list.html'
    model = Blog

    def get_queryset(self):
        kind = self.kwargs['kind']
        if kind == 'main':
            return Blog.objects.filter(kind=Blog.MAIN)
        elif kind == 'enterprise':
            return Blog.objects.filter(kind=Blog.ENTERPRISE)
        else:
            raise Http404()