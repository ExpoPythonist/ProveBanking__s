from django.conf.urls import patterns, url

from med_social.decorators import (member_required,
                                   admin_required)
from . import views

UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

urlpatterns = [
    url(r'^$', admin_required(views.UsersList.as_view()), name='list'),
    url(r'^notifications/mark_read/$', views.mark_notifs_read, name='mark_notifs_read'),
    url(r'^notifications/all/$', views.all_notifications, name='all_notifications'),
    url(r'^notifications/read/$', views.read_notifications, name='read_notifications'),
    url(r'^notifications/unread/$', views.unread_notifications, name='unread_notifications'),
    url(r'^join/(?P<uuid>{})'.format(UUID), views.UserDirectJoinView.as_view(), name='direct_join'),
    url(r'^signups/$', views.signups, name='signups'),
    url(r'^signups/(?P<pk>\d+)/approve/$', views.signup_approve, name='signup_approve'),
    url(r'^signups/(?P<pk>\d+)/reject/$', views.signup_delete, name='signup_delete'),
    url(r'^invite/$', views.user_invite_view, name='invite'),
    url(r'^register/$', views.user_register_view, name='register'),
    url(r'^register/confirm/(?P<uuid>{})'.format(UUID), views.user_confirm_view, name='confirm_register'),
    url(r'^search/$', member_required(views.user_search), name='search'),
    url(r'^invite/(?P<pk>\d+)/$', views.user_direct_invite_view, name='direct_invite'),
    url(r'^invite/resend/(?P<pk>\d+)/$', views.user_resend_invite_view, name='resend_invite'),
    url(r'^(?P<pk>\d+)/delete/$', admin_required(views.UserDelete.as_view()), name='delete'),
    url(r'^(?P<pk>\d+)/permissions/$', views.UserPermissionsUpdate.as_view(), name='edit_permission'),
    url(r'^(?P<pk>\d+)/$', member_required(views.ProfileByID.as_view()), name='profile_by_id'),
    url(r'^(?P<username>[\w+.-]+)/$', member_required(views.ProfileDetails.as_view()), name='profile'),
    url(r'^(?P<username>[\w+.-]+)/modal/$', member_required(views.ProfileModalDetails.as_view()), name='profile_modal'),
    url(r'^(?P<username>[\w+.-]+)/allocation/add/$', views.add_allocation, name='add_allocation'),
    url(r'^(?P<username>[\w+.-]+)/allocation/(?P<pk>\d+)/edit/$', views.edit_allocation, name='edit_allocation'),
    url(r'^(?P<username>[\w+.-]+)/edit/$', views.profile_edit_view, name='edit_profile'),
    url(r'^password/reset/$', views.password_reset_view, name='password_reset'),
    url(r'^uploads/avatar/(?P<userid>\d+)/$', views.upload_avatar, name='upload_avatar'),
    url(r'^@(?P<username>[\w+-]+)/settings/notifications/$', views.settings_notifications, name='settings_notifications'),
]
