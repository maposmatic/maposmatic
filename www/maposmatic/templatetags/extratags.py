# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2009  David Decotigny
# Copyright (C) 2009  Frédéric Lehobey
# Copyright (C) 2009  David Mentré
# Copyright (C) 2009  Maxime Petazzoni
# Copyright (C) 2009  Thomas Petazzoni
# Copyright (C) 2009  Gaël Utard

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
import datetime

register = template.Library()

def job_status_to_str(value, arg, autoescape=None):

    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x

    if value == 0:
        result = _("Waiting rendering")
    elif value == 1:
        result = _("Rendering in progress")
    elif value == 2:
        if arg == "okx":
            result = _("Rendering successful")
        else:
            result = _("Rendering failed, please contact " \
                       "<a href=\"mailto:contact@maposmatic.org\">" \
                       "contact@maposmatic.org</a>")
    else:
        result = ""

    return mark_safe(result)

job_status_to_str.needs_autoescape = True

def feedparsed(value):
    return datetime.datetime(*value[:6])

register.filter('job_status_to_str', job_status_to_str)
register.filter('feedparsed', feedparsed)
