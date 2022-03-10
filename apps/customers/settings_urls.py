from django.conf.urls import patterns, include, url

from med_social.decorators import admin_required
from .views.settings import (SettingsHome, MetricList, MetricTypeList, EditMetric, CategoryList, CreateCategory,
                             EditCategory, DeleteCategory)

from locations import views as location_views
from customers import views


# namespace = client_settings
urlpatterns = [
    url(r'^$', admin_required(SettingsHome.as_view()), name='home'),
    url(r'^features/$', admin_required(views.feature_list), name='features'),
    url(r'^weights/$', admin_required(views.weights), name='weights'),
    url(r'^premium/$', admin_required(views.premium_settings), name='premium'),
    url(r'^metrics/$', admin_required(MetricTypeList.as_view()), name='metrics_type_list'),
    url(r'^metrics/for/(?P<ctype_id>\d+)/$', admin_required(MetricList.as_view()), name='metrics_list'),
    url(r'^metrics/for/(?P<ctype_id>\d+)/(?P<pk>\d+)/edit/$', admin_required(EditMetric.as_view()),
        name='edit_metric'),
    url(r'^metrics/for/(?P<ctype_id>\d+)/create/$', admin_required(EditMetric.as_view()), name='create_metric'),
    url(r'^services/', include('services.urls.clients', namespace='services')),
    url(r'^c/(?P<kind>\w+)/$', admin_required(CategoryList.as_view()), name='manage_categories'),
    url(r'^c/(?P<kind>\w+)/create/$', admin_required(CreateCategory.as_view()), name='create_category'),
    url(r'^c/(?P<kind>\w+)/edit/(?P<pk>\d+)/$', admin_required(EditCategory.as_view()), name='edit_category'),
    url(r'^c/(?P<kind>\w+)/delete/(?P<pk>\d+)/$', admin_required(DeleteCategory.as_view()), name='delete_category'),
    url(r'^locations/$', admin_required(location_views.LocationList.as_view()), name='location_list'),
    url(r'^locations/create/$', admin_required(location_views.CreateLocations.as_view()), name='create_location'),
    url(r'^locations/(?P<pk>\d+)/edit/$', admin_required(location_views.EditLocations.as_view()),
        name='edit_location'),
    url(r'^roles/', include('roles.urls', namespace='roles')),
    url(r'^skill-levels/', include('categories.urls.skill_levels', namespace='skill_levels')),
]
