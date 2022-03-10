from simple_activity import registry
from simple_activity.verbs import BaseVerb


@registry.register
class Edit(BaseVerb):
    code = 'edit'
    past_tense = 'edited'


@registry.register
class Create(BaseVerb):
    code = 'create'
    past_tense = 'created'


@registry.register
class Invite(BaseVerb):
    code = 'invite'
    past_tense = 'invited'


@registry.register
class Join(BaseVerb):
    code = 'join'
    past_tense = 'joined'
    template_name = 'activity/actions/join.html'
