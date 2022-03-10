import urllib
from django.db import models
from django.utils.encoding import smart_text
from django_pgjson.fields import JsonBField

from urlobject import URLObject

from med_social.utils import to_base64_md5


def _default_dict():
    return {}


def _default_list():
    return []


class Search(models.Model):
    hashed = models.CharField(unique=True, db_index=True, max_length=22)
    keyword = models.TextField()
    results = models.ManyToManyField('Result', related_name='searches')
    last_searched = models.DateTimeField(null=True, blank=True)

    def save_results(self, results):
        all_results = []
        for result in results:
            result['url'] = URLObject(smart_text(urllib.unquote(result['url']))).without_query()
            db_result, created = Result.objects.get_or_create(hashed=to_base64_md5(result['url'].encode('utf-8')))
            all_results.append(db_result)
            if created:
                db_result.meta = result
                db_result.save()
            else:
                sources = db_result.meta.get('sources', [])
                sources.extend(result['sources'])
                db_result.meta['sources'] = list(set(sources))
                db_result.save()

        result_ids = [r.id for r in all_results]
        present = self.results.filter(id__in=result_ids).values_list('id', flat=True)

        new_ones = [r for r in result_ids if r not in present]
        self.results.add(*new_ones)


class Result(models.Model):
    """
    `hashed` should be base64 encoded md5 hash of the URL

    `result.meta` should look like this.
        {
            'url': URL, # URL
            'title': TEXT # Title of the article
            'date': NUMBER, # data in Javascript compatible epoch
            'site': URL, # name of the site
            'siteurl': TEXT # url of the site
            'summary': TEXT # summary
            'sources': ARRAY[TEXT] # google | yahoo | faroo | bing | ??

        }
    """

    hashed = models.TextField(db_index=True, unique=True)
    meta = JsonBField(default=_default_dict)
    created = models.DateTimeField(auto_now_add=True)
