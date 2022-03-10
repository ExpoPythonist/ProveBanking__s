from django.views.generic import (ListView,
                                  CreateView,
                                  UpdateView)
from django.core.urlresolvers import reverse_lazy
from med_social.decorators import client_required

from ..models import SkillLevel


class SkillLevelList(ListView):
    model = SkillLevel
    context_object_name = 'skill_levels'
    template_name = 'skills/levels/list.html'
skill_level_list = client_required(SkillLevelList.as_view())


class CreateSkillLevel(CreateView):
    model = SkillLevel
    fields = ('label', 'level')
    template_name = 'skills/levels/form.html'
    success_url = reverse_lazy('client_settings:skill_levels:list')

    def get_context_data(self, *args, **kwargs):
        context = super(CreateSkillLevel, self).get_context_data(*args,
                                                                 **kwargs)
        context['action_label'] = 'create'
        return context
create_skill_level = client_required(CreateSkillLevel.as_view())


class EditSkillLevel(UpdateView):
    model = SkillLevel
    fields = ('label', 'level')
    template_name = 'skills/levels/form.html'
    success_url = reverse_lazy('client_settings:skill_levels:list')

    def get_context_data(self, *args, **kwargs):
        context = super(EditSkillLevel, self).get_context_data(*args, **kwargs)
        context['action_label'] = 'edit'
        return context
edit_skill_level = client_required(EditSkillLevel.as_view())
