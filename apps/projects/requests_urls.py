from django.conf.urls import patterns, url, include

from med_social.decorators import (client_required, vendor_required,
                                   member_required)
from .views import (StaffingRequestDetails,
                    CreateResponse, ResponseDetails,
                    accept_response, RemoveStaffFromProject,
                    CreateStaffingResponse, UserSuggestions,
                    VendorSuggestions, UsersAddList, VendorAddList,
                    CreateDeliverableResponse)
from .views import staffing

urlpatterns = patterns('',
    url(r'^add_vendors/$', staffing.add_vendors,
        name='add_vendors'),
    url(r'^(?P<project_pk>\d+)/create/(?P<request_kind>({}))/$'.format('|'.join(staffing.StaffingRequestCreateView.model.KIND_NAMES.values())),
        staffing.staffing_request_create,
        name='create'),

    url(r'^create/(?P<request_kind>({}))/$'.format('|'.join(staffing.StaffingRequestCreateView.model.KIND_NAMES.values())),
        staffing.staffing_request_create,
        name='create'),

    url(r'^s/(?P<pk>\d+)/edit/$', staffing.staffing_basic,
        name='edit'),
    url(r'^s/(?P<pk>\d+)/advanced/$', staffing.staffing_advanced,
        name='edit_advanced'),

    url(r'^user/suggestions/$', client_required(UserSuggestions.as_view()),
        name='user_suggestions'),
    url(r'^vendor/suggestions/$', client_required(VendorSuggestions.as_view()),
        name='vendor_suggestions'),


    url(r'^s/(?P<pk>\d+)/delete/$', staffing.delete_draft,
        name='delete_draft'),

    url(r'^(?P<stfrq_pk>\d+)/$', member_required(StaffingRequestDetails.as_view()),
        name='detail'),
    url(r'^(?P<stfrq_pk>\d+)/respond/$', vendor_required(CreateDeliverableResponse.as_view()),
        name='response'),
    url(r'^(?P<stfrq_pk>\d+)/respond/(?P<response_id>\d+)/$', vendor_required(CreateResponse.as_view()),
        name='edit_fixed_response'),
    url(r'^(?P<stfrq_pk>\d+)/create_staffing_response/$', vendor_required(CreateStaffingResponse.as_view()),
        name='create_staffing_response'),
    url(r'^(?P<stfrq_pk>\d+)/(?P<response_id>\d+)/$',
        member_required(ResponseDetails.as_view()), name='response_details'),
    url(r'^(?P<stfrq_pk>\d+)/(?P<response_pk>\d+)/accept/$',
        client_required(accept_response), name='response_accept'),
    url(r'^(?P<stfrq_pk>\d+)/reviews/',
        include('reviews.urls', namespace='reviews')),
    url(r'^(?P<stfrq_pk>\d+)/user/add/$', client_required(UsersAddList.as_view()),
        name='add_user_request'),
    url(r'^(?P<stfrq_pk>\d+)/vendor/add/$', client_required(VendorAddList.as_view()),
        name='add_vendor_request'),
)
