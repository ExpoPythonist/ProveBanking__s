from django import template


register = template.Library()


@register.assignment_tag
def get_unread_notifications(user, limit=5):
    return user.notifications.filter(unread=True)[:limit]
