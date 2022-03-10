from datetime import timedelta

from django.utils.timezone import now
from annoying.functions import get_object_or_None
from celery import Task, task, chord

from med_social.utils import get_redis
from aggregators.utils import hash_query
from .models import Search
from .utils import make_search_job_key
from .sources import yahoo, faroo, google


class SetUpTask(Task):
    abstract = True

    def apply_async(self, args, kwargs, *m_args, **m_kwargs):
        if args:
            query = args[0]
        else:
            query = kwargs.get('query')
        job_key = make_search_job_key(query)
        r = get_redis()
        if r.get(job_key):
            return
        r.set(job_key, True)
        r.expire(job_key, 120)
        kwargs['job_key'] = job_key
        super(SetUpTask, self).apply_async(args, kwargs, *m_args, **m_kwargs)


class CleanUpMixin(object):
    def cleanup(self, job_key):
        r = get_redis()
        r.delete(job_key)


class CleanUpOnReturnTask(Task, CleanUpMixin):
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        self.cleanup(kwargs['job_key'])
        return super(CleanUpOnReturnTask, self).after_return(status, retval, task_id, args, kwargs, einfo)


class CleanUpOnFailureTask(Task, CleanUpMixin):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.cleanup(kwargs['job_key'])
        return super(CleanUpOnFailureTask, self).on_failure(exc, task_id, args, kwargs, einfo)


@task(ignore_result=False, base=CleanUpOnFailureTask)
def search_yahoo(query, job_key):
    return yahoo.search(query)


@task(ignore_result=False, base=CleanUpOnFailureTask)
def search_faroo(query, job_key):
    return faroo.search(query)


@task(ignore_result=False, base=CleanUpOnFailureTask)
def search_google(query, job_key):
    return google.search(query)


@task(base=CleanUpOnReturnTask)
def process_news(results, search_id, job_key):
    search = get_object_or_None(Search, id=search_id)
    if not search:
        return

    results = reduce(lambda res, current: res + current, results)
    search.save_results(results)
    search.last_searched = now()
    search.save()


@task(base=SetUpTask)
def search_news_task(query, job_key):
    search, created = Search.objects.get_or_create(hashed=hash_query(query), defaults={'keyword': query})
    if not created:
        one_hour_ago = now() - timedelta(hours=1)
        if search.last_searched and (search.last_searched > one_hour_ago):
            return
    #fetch_news = [search_yahoo.s(query, job_key=job_key),
    #              search_faroo.s(query, job_key=job_key),
    #              search_google.s(query, job_key=job_key),]

    fetch_news = [search_google.s(query, job_key=job_key),]
    chord(fetch_news)(process_news.s(search.id, job_key=job_key))
