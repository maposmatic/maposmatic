from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

def job_status_to_str(value, arg, autoescape=None):

    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x

    if value == 0:
        result = "Waiting rendering"
    elif value == 1:
        result = "Rendering in progress"
    elif value == 2:
        if arg == "ok":
            result = "Rendering successfull"
        else:
            result = "Rendering failed, reason: <i>%s</i>" % esc(arg)
    else:
        result = ""

    return mark_safe(result)

job_status_to_str.needs_autoescape = True

register.filter('job_status_to_str', job_status_to_str)
