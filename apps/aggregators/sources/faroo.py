import requests
from requests import ConnectionError

from django.conf import settings

from med_social.utils import escape_unicode_dict

__all__ = ('search',)

url = 'http://www.faroo.com/api?q={query}&start=1&length=10&l=en&src=news&i=false&f=json&key={key}'


def build_url(query):
    return url.format(query=query, key=settings.FAROO_KEY)


def search(query):
    # TODO: set up logging for bad calls
    try:
        response = requests.get(build_url(query))
    except ConnectionError:
        return []

    if not response.ok:
        return []

    try:
        response = response.json()
    except ValueError:
        return []

    results = response.get('results')

    if results:
        return [escape_unicode_dict({
            'url': R['url'],
            'title': R['title'],
            'date': R['date'],
            'site': R['domain'],
            'siteurl': R['domain'],
            'summary': R['kwic'],
            'sources': ['faroo']
        }) for R in results]
    else:
        return []
