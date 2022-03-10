from django.contrib.auth.models import Group

CLIENT_GROUPS = (
    # ('name', 'display name', 'is_admin',),
    ('client:admin', 'Admin', Group.DEFAULT_ADMIN),
    ('client:user', 'User', Group.DEFAULT_USER),
)
