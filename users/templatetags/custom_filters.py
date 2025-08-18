from django import template
from users.models import User

register = template.Library()

@register.filter
def split(value, key=','):
    return value.split(key)

@register.filter
def get_important_points_display(value):
    choices = value.split(',') if value else []
    important_choices_dict = dict(User.IMPORTANT_CHOICES)
    display_texts = [important_choices_dict.get(c, c) for c in choices]
    return ', '.join(display_texts)
