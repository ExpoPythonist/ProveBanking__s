from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required

from .views import HomeView, CreateForAutocomplete, ProjectsStatus, MyProjectsStatus, VendorSearch


urlpatterns = [
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^search/$', login_required(VendorSearch.as_view()), name='search'),
    url(r'^status/$', login_required(ProjectsStatus.as_view()), name='projects_status'),
    url(r'^mystatus/$', login_required(MyProjectsStatus.as_view()), name='my_projects_status'),
    url(r'^settings/', include('customers.settings_urls', namespace='client_settings')),
    url(r'^core/autocomplete/(?P<content_type_pk>\d+)/create/$',
        login_required(CreateForAutocomplete.as_view()), name='create_for_autocomplete'),
]
