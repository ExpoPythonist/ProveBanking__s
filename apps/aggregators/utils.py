import re
from hashlib import md5

import six

from med_social.utils import to_base64_md5, get_redis

regex_template = r'((\w+\W+){{0,{adjacency}}}{keyword}(\W+\w+){{0,{adjacency}}})'


def is_updating(keyword=None, hashed=None):
    if not (keyword or hashed):
        raise ValueError('`is_updating` required either the keyword or '
                         'hashed keyword to work')
    r = get_redis()
    if keyword:
        hashed = make_search_job_key(keyword)
    return bool(r.get(hashed))


def find_with_adjacent_words(blob, keyword, adjacent_words=25):
    regex = regex_template.format(keyword=keyword, adjacency=adjacent_words)
    match = re.search(regex, blob)
    if match and match.groups():
        return match.groups()[0]


def make_search_job_key(query):
    if six.PY2 and isinstance(query, six.text_type):
        query = query.encode('utf8')

    return md5('search:{}'.format(query)).hexdigest()


def hash_query(query):
    return to_base64_md5(query, also_lower=True, also_slugify=True)
