from django import template
from room.models import (
    OPTION_CHOICES,
    SECURITY_CHOICES,
    OTHER_FACILITY_CHOICES,
    HEATING_CHOICES,
)

register = template.Library()

def _to_dict(choices):
    # [('WASHER','세탁기'), ...] -> {'WASHER':'세탁기', ...}
    return {k: v for k, v in choices}

_opt = _to_dict(OPTION_CHOICES)
_sec = _to_dict(SECURITY_CHOICES)
_oth = _to_dict(OTHER_FACILITY_CHOICES)
_heat = _to_dict(HEATING_CHOICES)

@register.filter(name="label_option")
def label_option(code):
    return _opt.get(code, code)

@register.filter(name="label_security")
def label_security(code):
    return _sec.get(code, code)

@register.filter(name="label_other")
def label_other(code):
    return _oth.get(code, code)

@register.filter(name="label_heating")
def label_heating(code):
    return _heat.get(code, code)
