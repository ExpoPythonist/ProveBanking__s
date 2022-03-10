import random
import datetime

from braces.views import JSONResponseMixin
from django.views.generic import TemplateView, DetailView
from med_social.decorators import client_required
from projects.models import ProposedResourceStatus, StaffingRequest
from .forms import chartform


class InsightCharts(TemplateView):
    template_name = 'analytics/home.html'

    def get_context_data(self, **kwargs):
        ctx = super(InsightCharts, self).get_context_data()
        form = chartform(data=self.request.GET)
        if form:ctx['form'] = form
        return ctx
home = client_required(InsightCharts.as_view())


class Charts(JSONResponseMixin, DetailView):

    def get(self, request, *args, **kwargs):

        ctx = self.get_context_data(**kwargs)
        response = {}
        response['data'] = ctx['chartdata']
        if 'location' in ctx:
            response['location'] = ctx['location']
        return self.render_json_response(response)

    def get_context_data(self, **kwargs):
        ctx = {}
        form = chartform(data=self.request.GET)
        form.is_valid()
        location = form.cleaned_data.get('location')
        skills = form.cleaned_data.get('skills')

        requests = StaffingRequest.objects.filter(
            kind=StaffingRequest.KIND_STAFFING,
            proposed__status__value=ProposedResourceStatus.SUCCESS)
        if location:
            requests = requests.filter(location=location)

        ctx['chartdata'] = self.get_data(requests, skills)
        if location:
            ctx['location'] = location.city
        if form:ctx['form'] = form
        return ctx


class CycleTimeChart(Charts):

    def get_data(self, staffingrequests, skills):
        chartdata = []
        requests = staffingrequests
        if not skills:
            skilldata = 12 * [0]
            monthlist = requests.datetimes('created', 'month')
            for month in monthlist:
                staffrequests = requests.filter(created__month=month.month)
                avgtime = staffrequests.extra(select={'time':
                        '(status_changed_at - projects_staffingrequest.created)'
                                                 }).values_list('time', flat=True)
                avgtime = sum(avgtime, datetime.timedelta()) / len(avgtime)
                if avgtime is not None:
                    avgtime = (avgtime.days +
                               float(avgtime.seconds) / float(24 * 3600))
                    avgtime = float("{:.1f}".format(avgtime))
                else:
                    avgtime = 0
                skilldata[month.month - 1] = avgtime

            col = 'OrangeRed'
            chartdata.append({'data': skilldata, 'fillColor': col,
                              'strokeColor': col, 'pointStrokeColor': '#fff',
                              'pointColor': col, 'pointHighlightFill': '#fff',
                              'pointHighlightStroke': 'black', 'title': 'All'
                              })
        if skills:
            colornames = ['#F282C7','#43444F','#878BB6', '#FF8153', '#49CAB4']
            for skill in skills:
                if not colornames:
                    random.seed(skill)
                    r = lambda: random.randint(0, 255)
                    col = ('#%02X%02X%02X' % (r(), r(), r()))
                if colornames:
                    col = colornames.pop()

                skilldata = 12 * [0]
                requests2 = requests.filter(categories=skill)
                monthlist = requests2.datetimes('created', 'month')
                for month in monthlist:
                    staffrequests = requests2.filter(created__month=month.month)
                    avgtime = staffrequests.extra(select={'time':
                        '(status_changed_at - projects_staffingrequest.created)'
                                                 }).values_list('time', flat=True)
                    avgtime = sum(avgtime, datetime.timedelta()) / len(avgtime)
                    if avgtime is not None:
                        avgtime = (avgtime.days +
                                   float(avgtime.seconds) / float(24 * 3600))
                        avgtime = float("{:.1f}".format(avgtime))
                    else:
                        avgtime = 0
                    skilldata[month.month - 1] = avgtime

                chartdata.append({'title': skill.name.encode('utf-8'),
                                  'fillColor': col, 'pointStrokeColor': '#fff',
                                  'pointHighlightFill': '#fff',
                                  'data': skilldata,
                                  'pointColor': col, 'strokeColor': col,
                                  'pointHighlightStroke': 'black'})
        return chartdata
cycletime = client_required(CycleTimeChart.as_view())


class PeopleStaffedChart(Charts):

    def get_data(self, staffingrequests, skills):
        chartdata = []
        requests = staffingrequests
        if not skills:
            count = 12 * [0]
            monthlist = requests.datetimes('created', 'month')
            for month in monthlist:
                count[month.month - 1] = requests.filter(
                    created__month=month.month).count()
            col = 'OrangeRed'
            chartdata.append({'title': 'All', 'pointHighlightStroke': 'black',
                              'fillColor': col, 'strokeColor': col,
                              'pointColor': col, 'pointStrokeColor': '#fff',
                              'pointHighlightFill': '#fff',
                              'data': count})
        if skills:
            colornames = ['#F282C7','#43444F','#878BB6', '#FF8153', '#49CAB4']
            for skill in skills:
                if not colornames:
                    random.seed(skill)
                    r = lambda: random.randint(0, 255)
                    col = ('#%02X%02X%02X' % (r(), r(), r()))
                if colornames:
                    col = colornames.pop()

                count = 12 * [0]
                requests2 = requests.filter(categories=skill)
                monthlist = requests2.datetimes('created', 'month')
                for month in monthlist:
                    count[month.month - 1] = requests2.filter(
                        created__month=month.month).count()
                chartdata.append({'title': skill.name.encode('utf-8'),
                                  'fillColor': col, 'pointStrokeColor': '#fff',
                                  'strokeColor': col, 'pointColor': col,
                                  'pointHighlightFill': '#fff', 'data': count,
                                  'pointHighlightStroke': 'black'
                                  })
        return chartdata
peoplestaffed = client_required(PeopleStaffedChart.as_view())
