from django.conf.urls import patterns, url, include

from med_social.decorators import (member_required, vendor_required, client_required)

from .views import (CreateProject, UpdateProject, ProjectDetails,
                    ProjectBudget, SendProposalView, budget_details,project_list,
                    my_project_list, staffing_confirmation, add_user_to_project,
                    share_project, change_proposed_status, invite_users)


urlpatterns = patterns('projects.views',
    url(r'^$', project_list, name='list'),
    url(r'^my/$', my_project_list, name='my_list'),
    url(r'^create/$', member_required(CreateProject.as_view()), name='create'),
    url(r'^(?P<pk>\d+)/$', member_required(ProjectDetails.as_view()),
        name='detail'),
    url(r'^(?P<pk>\d+)/users/add/$', add_user_to_project,
        name='add_user'),
    url(r'^(?P<pk>\d+)/budget/$', member_required(ProjectBudget.as_view()),
        name='budget_label'),
    url(r'^(?P<pk>\d+)/budget/details/$', budget_details,
        name='budget_details'),
    url(r'^(?P<pk>\d+)/edit/$', UpdateProject.as_view(), name='edit'),
    #url(r'^(?P<pk>\d+)/status/edit/$', 'update_project_status', name='edit_status'),
    url(r'^(?P<project_pk>\d+)/proposed/(?P<pk>\d+)/status/$',
        change_proposed_status,
        name='change_proposed_status'
    ),
    url('responses/send_proposal/(?P<pk>\d+)/$',
        vendor_required(SendProposalView.as_view()),
        name='send_proposal'
    ),
    url('users/invite/$', invite_users, name='invite_users'),
    url('status/', include('projects.status_urls', namespace='status')),
    url(r'^confirm/(?P<sr_pk>\d+)/(?P<answer>\d+)/$',
        vendor_required(staffing_confirmation),
        name='staffing_confirmation'),
    url(r'^(?P<project_pk>\d+)/team/$',
        client_required(share_project),
        name='share_project'),
)
