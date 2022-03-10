from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required

from med_social.decorators import member_required

from users.views import (CreateOnboardingUserProfileView,
    CreateOnboardingVendorProfileView, run_setup_wizard, WelcomeStep,
    LinkedinUserProfileView, PasswordSetView)

from users.views import (vendor_profile_detail,
                         vendor_profile_basic,
                         vendor_profile_web,)

from vendors.views import (VendorProjectEdit,
                           VendorLocationList,
                           VendorSkillList,
                           VendorRoleList,
                           VendorServicesList,
                           VendorIndustryList,)
from .models import User


'''
Genrates url for each setup step as with

   path as '/setup/step/{{STEP}}/'

and

    name as 'setup_step_{{STEP_LABEL}}'

To add a new step, add it to the routes dictionary above with the view as the value
'''
routes = {
    User.SETUP_PASSWORD_SET: PasswordSetView.as_view(),
    User.SETUP_LINKEDIN_FETCH: LinkedinUserProfileView.as_view(),
    User.SETUP_USER_PROFILE: CreateOnboardingUserProfileView.as_view(),
    User.SETUP_WELCOME: WelcomeStep.as_view(),
}

urlpatterns = patterns('',
    url(r'^wizard/$', run_setup_wizard, name='run_setup_wizard'),
    url(r'^%d/(?P<pk>\d+)/$' % User.SETUP_VENDOR_PROFILE, vendor_profile_basic, name='setup_step_%s' % User.SETUP_STEPS_DICT[User.SETUP_VENDOR_PROFILE]),
    
    url(r'^%d/(?P<pk>\d+)/project/$' % User.SETUP_VENDOR_PROFILE, member_required(VendorProjectEdit.as_view()), name='setup_step_vendor_projects'),
    url(r'^%d/(?P<pk>\d+)/web/$' % User.SETUP_VENDOR_PROFILE, vendor_profile_web, name='setup_step_vendor_media'),
    url(r'^%d/(?P<pk>\d+)/location/$' % User.SETUP_VENDOR_PROFILE, member_required(VendorLocationList.as_view()), name='setup_step_vendor_location'),
    url(r'^%d/(?P<pk>\d+)/service/$' % User.SETUP_VENDOR_PROFILE, member_required(VendorServicesList.as_view()), name='setup_step_vendor_service'),
    url(r'^%d/(?P<pk>\d+)/skill/$' % User.SETUP_VENDOR_PROFILE, member_required(VendorSkillList.as_view()), name='setup_step_vendor_skill'),
    url(r'^%d/(?P<pk>\d+)/role/$' % User.SETUP_VENDOR_PROFILE, member_required(VendorRoleList.as_view()), name='setup_step_vendor_role'),
    url(r'^%d/(?P<pk>\d+)/industries/$' % User.SETUP_VENDOR_PROFILE, member_required(VendorIndustryList.as_view()), name='setup_step_vendor_industries'),
    *[url(r'^%d/$' % key, login_required(value), name='setup_step_%s' % User.SETUP_STEPS_DICT[key])
    for key, value in routes.items()]
)
