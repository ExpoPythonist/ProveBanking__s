from django.conf import settings

from yahooboss import BossSearch

from med_social.utils import escape_unicode_dict


__all__ = ('search',)


boss_search = BossSearch(settings.BOSS_KEY, settings.BOSS_SECRET)


def search(query):
    results = boss_search.search_news(query)
    if results:
        return [escape_unicode_dict({
            'url': R['url'],
            'title': R['title'],
            'date': R['date'] * 1000 if 'date' in R else None,
            'site': R['source'],
            'siteurl': R['sourceurl'],
            'summary': R['abstract'],
            'sources': ['yahoo']
        }) for R in results]
    else:
        return []
