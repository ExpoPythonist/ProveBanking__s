import urllib
from rest_framework import serializers

from med_social.utils import unescape_unicode_dict
from aggregators.utils import hash_query, is_updating
from aggregators.models import Search, Result
from vendors.models import Vendor



__all__ = ('AggregatorSerializer', 'ResultSerializer', 'VendorNewsSerializer')



class ResultSerializer(serializers.ModelSerializer):
    meta = serializers.SerializerMethodField()
    keywords = serializers.SerializerMethodField()

    class Meta:
        model = Result
        fields = ('id', 'meta', 'keywords',)

    def get_keywords(self, obj):
        return obj.searches.filter(hashed__in=self.context['hashes']).values_list('keyword')

    def get_meta(self, obj):
        if obj.meta:
            meta = obj.meta.copy()
            meta['url'] = urllib.unquote(meta['url'].encode('utf-8'))
            return unescape_unicode_dict(meta)
        else:
            return {}


class AggregatorSerializer(serializers.ModelSerializer):
    results = serializers.SerializerMethodField()
    is_updating = serializers.SerializerMethodField()

    class Meta:
        model = Search
        fields = ('id', 'is_updating', 'keyword', 'results',)

    def get_results(self, obj):
        return ResultSerializer(obj.results.all(), many=True,
                                context={'keyword': obj.keyword}).data

    def get_is_updating(self, obj):
        return is_updating(keyword=obj.keyword)


class VendorNewsSerializer(serializers.ModelSerializer):
    results = serializers.SerializerMethodField()
    keywords = serializers.SerializerMethodField()
    is_updating = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = ('id', 'is_updating', 'keywords', 'results',)

    def get_is_updating(self, vendor):
        # FiXME: move this to bulk operation
        for keyword in vendor.get_search_keywords():
            if is_updating(keyword=keyword):
                return True
        return False

    def get_keywords(self, vendor):
        return vendor.get_search_keywords()

    def get_results(self, vendor):
        hashes = [hash_query(keyword)
                  for keyword in vendor.get_search_keywords()]
        return ResultSerializer(
            Result.objects.filter(searches__hashed__in=hashes),
            many=True, context={'hashes': hashes}).data
