from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from django.conf import settings

from mailviews import previews
# Uncomment the next two lines to enable the admin:
from django.contrib import admin

from .views import (HomeView, WaitListView, InviteView, InviteApplyView, ThankYou, About, HeartBeat, GetVetted)
from .views.site import RequestDemoView
from customers.views import ClientInviteRequestView, CreateForAutocomplete
from customers import public_views
from .decorators import member_required
from .admin import site as admin_site

previews.autodiscover()
admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    url(r'^api/', include('API.public_urls', namespace='public_api')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^aggregators/', include('aggregators.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^emails/', include(previews.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^requestinvite/', ClientInviteRequestView.as_view(), name='client_invite_request'),
    url(r'^avatar/', include('avatar.urls')),
    url(r'^waitlist/$', login_required(WaitListView.as_view()), name='waitlist'),
    url(r'^contact/$', TemplateView.as_view(template_name="contact_us.html"), name='contact_us'),
    url(r'^about/$', TemplateView.as_view(template_name="about.html"), name='about'),
    url(r'^redactor/', include('redactor.urls')),
    url(r'^invite/$', member_required(InviteView.as_view()), name='invite'),
    url(r'^apply/@(?P<username>%s)/$' % settings.ACCOUNT_USERNAME_REGEX, InviteApplyView.as_view(), name='invite_link'),
    url(r'^blog/', include('blog.urls', namespace='blogs')),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'), name='about'),
    url(r'^users/', include('users.urls', namespace='users')),
    url(r'^u/', include('users.setup_urls', namespace='user_setup')),
    url(r'^request/$', RequestDemoView.as_view(), name='requestdemo'),
    url(r'^thankyou/$', ThankYou.as_view(), name='thankyou'),
    url(r'^get/$', GetVetted.as_view(), name='get_vetted'),
    url(r'^about/$', About.as_view(), name='about'),
    url(r'^heartbeat/$', HeartBeat.as_view(), name='heartbeat'),
    url(r'^p/heartbeat/$', HeartBeat.as_view(), name='public_heartbeat'),
    url(r'^locations/', include('locations.urls', namespace='locations')),
    url(r'^core/autocomplete/(?P<content_type_pk>\d+)/create/$',
        login_required(CreateForAutocomplete.as_view()), name='create_for_autocomplete'),
    url(r'^GVajMb45WHgMHQn.WqiOZXgU55JBTVYxudk3frta7Q--.html$',
        TemplateView.as_view(template_name='yahoo-verification.html'),
        name='yahoo-verification'),
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^(?P<slug>[\w-]+)/$', public_views.community_view, name='community_view'),
)

# Serve static files in development
urlpatterns += staticfiles_urlpatterns()
if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )

admin.site.login = admin_site.login

# Usefull for testing prod environment locally without nginx
# urlpatterns += patterns('',
#     url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
#         'document_root': settings.STATIC_ROOT,
#     }),
# )
