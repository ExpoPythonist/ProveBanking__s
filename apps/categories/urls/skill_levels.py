from django.conf.urls import patterns, url

from categories.views import skill_levels
from med_social.decorators import admin_required


urlpatterns = [
    url(r'^$', skill_levels.skill_level_list, name='list'),
    url(r'^create/$', admin_required(skill_levels.create_skill_level), name='create'),
    url(r'^(?P<pk>\d+)/edit/$', skill_levels.edit_skill_level, name='edit'),
]
