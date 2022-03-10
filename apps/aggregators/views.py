from django.views.generic import ListView

from .models import Result
from .tasks import search_news_task


class SearchView(ListView):
    template_name = 'aggregator/results.html'
    context_object_name = 'results'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if query:
            self.object_list = self.perform_search(query)
        else:
           self.object_list =  []
        ctx = self.get_context_data()
        return self.render_to_response(ctx)


class SearchNews(SearchView):
    def perform_search(self, query):
        search_news_task.delay(query)
        return Result.objects.filter(keywords__contains=query)
