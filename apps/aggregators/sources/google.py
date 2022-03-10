from time import mktime
from django.conf import settings

from urlobject import URLObject
import feedparser
import requests
from requests import ConnectionError

from med_social.utils import escape_unicode_dict, html2text


__all__ = ('search',)


url = 'https://news.google.com/?q={query}&output=rss'


def build_url(query):
    return url.format(query=query)


def search(query):
    try:
        response = requests.get(build_url(query))
    except ConnectionError:
        return []

    if not response.ok:
        return []

    results = feedparser.parse(response.content).get('entries')

    if results:
        processed = []
        for R in results:
            url = URLObject(R['link']).query_dict.get('url')

            if not url:
                continue
            date = R.get('published_parsed')
            if date:
                date = mktime(date) * 1000
            else:
                date = None

            processed.append(escape_unicode_dict({
                'url': url,
                'title': R['title'],
                'date': date,
                'summary': html2text(R['summary']),
                'site': URLObject(url).hostname,
                'siteurl': URLObject(url).hostname,
                'sources': ['google']
            }))
        return processed

    else:
        return []
