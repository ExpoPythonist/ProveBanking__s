import urllib, urlparse

from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib.staticfiles.storage import CachedFilesMixin, ManifestFilesMixin
from django.contrib.staticfiles.storage import CachedStaticFilesStorage
from pipeline.storage import GZIPMixin
from pipeline.storage import PipelineMixin, PipelineStorage
from storages.backends.s3boto import S3BotoStorage


def domain(url):
    return urlparse.urlparse(url).hostname


class LocalTestPipelineStorage(PipelineStorage):
    pass



class ManifestStorage(ManifestFilesMixin, PipelineStorage):
    pass


class S3PipelineStorage(PipelineMixin, CachedFilesMixin, S3BotoStorage):

    def __init__(self, *args, **kwargs):
        kwargs['custom_domain'] = domain(settings.STATIC_URL)
        kwargs['location'] = settings.STATIC_PREFIX
        super(S3PipelineStorage, self).__init__(*args, **kwargs)

    def url(self, *a, **kw):
        # http://stackoverflow.com/questions/11820566/inconsistent-signaturedoesnotmatch-amazon-s3-with-django-pipeline-s3boto-and-st/12262106#comment16459418_12262106
        s = super(S3PipelineStorage, self).url(*a, **kw)
        if isinstance(s, unicode):
            s = s.encode('utf-8', 'ignore')
        scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
        path = urllib.quote(path, '/%')
        qs = urllib.quote_plus(qs, ':&=')
        return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))


class S3FileStorage(S3BotoStorage):
    def __init__(self, *args, **kwargs):
        kwargs['bucket'] = getattr(settings, 'AWS_MEDIA_BUCKET_NAME')
        super(S3FileStorage, self).__init__(*args, **kwargs)


if settings.USE_PROTECTED_FILE_STORAGE:
    protected_storage = S3BotoStorage(
        acl='private',
        querystring_auth=True,
        querystring_expire=600,  # 10 minutes, try to ensure people can't share
        bucket=getattr(settings, 'AWS_MEDIA_BUCKET_NAME')
    )
else:
    protected_storage = default_storage
