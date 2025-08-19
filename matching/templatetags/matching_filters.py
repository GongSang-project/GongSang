from django import template
from django.utils import timezone
from matching.utils import calculate_matching_score

register = template.Library()

@register.filter
def calculate_matching_score_filter(youth, owner):
    return calculate_matching_score(youth, owner)


@register.filter
def korean_timesince(d):
    now = timezone.now()
    diff = now - d

    if diff.days > 0:
        return f"{diff.days}일 전"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours}시간 전"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes}분 전"
    else:
        return "방금 전"