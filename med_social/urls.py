from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.conf import settings

from allauth.account.views import LoginView
from djangosaml2.views import echo_attributes
from mailviews import previews
previews.autodiscover()

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from notifications import urls as notifications_urls
admin.autodiscover()

from users.forms import CustomLoginForm
from .views import WaitListView, InviteView, InviteApplyView, About
from .decorators import member_required, client_required
from .admin import site as admin_site

urlpatterns = [
    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^emails/', include(previews.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    # We overrided some variables in allauth's original form implementation
    url(r'^accounts/login/$',
        LoginView.as_view(form_class=CustomLoginForm),
        name="account_login"),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^avatar/', include('avatar.urls')),
    url(r'^waitlist/$', login_required(WaitListView.as_view()), name='waitlist'),
    url(r'^contact/$', TemplateView.as_view(template_name='contact_us.html'), name='contact_us'),
    url(r'^about/$', About.as_view(), name='about'),
    url(r'^invite/$', member_required(InviteView.as_view()), name='invite'),
    url(r'^apply/@(?P<username>%s)/$' % settings.ACCOUNT_USERNAME_REGEX, InviteApplyView.as_view(), name='invite_link'),

    url(r'^api/', include('API.urls', namespace='api')),

    url(r'^projects/', include('projects.urls', namespace='projects')),
    url(r'^staffing/', include('projects.staffing_urls', namespace='staffing')),
    url(r'^availability/', include('availability.urls', namespace='availability')),
    url(r'^vendors/', include('vendors.urls', namespace='vendors')),
    url(r'^u/', include('users.setup_urls', namespace='user_setup')),
    url(r'^metrics/', include('reviews.metric_urls', namespace='metrics')),
    url(r'^users/', include('users.urls', namespace='users')),
    url(r'^notes/', include('notes.urls', namespace='notes')),
    url(r'^services/', include('services.urls.vendors', namespace='services')),
    url(r'^groups/', include('ACL.urls', namespace='groups')),
    url(r'^notifications/', include(notifications_urls)),
    url(r'^reviews/', include('reviews.urls', namespace='reviews')),
    url(r'^rates/', include('rates.urls', namespace='rates')),
    url(r'^channels/', include('channels.urls', namespace='channels')),
    url(r'^suggest/', include('core.suggestions_urls', namespace='suggestions')),
    url(r'^a/', include('analytics.urls', namespace='analytics')),
    url(r'^locations/', include('locations.urls', namespace='locations')),
    url(r'^divisions/', include('divisions.urls', namespace='divisions')),
    url(r'^clients/', include('clients.urls', namespace='clients')),
    url(r'', include('customers.urls')),
    url(r'^activity/', include('activity.urls', namespace='activity')),
    url(r'^blog/', include('posts.urls', namespace='posts')),
    url(r'^payments/', include('djstripe.urls', namespace='djstripe')),
    url(r'^saml2/', include('djangosaml2.urls')),
    url(r'^test/', echo_attributes),
    url(r'^rfp/', include('lightrfp.urls')),
]

# Serve static files in development
urlpatterns += staticfiles_urlpatterns()
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )

admin.site.login = admin_site.login

# Usefull for testing prod environment locally without nginx
#urlpatterns += patterns('',
#   url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
#       'document_root': settings.STATIC_ROOT,
#   }),
#)
