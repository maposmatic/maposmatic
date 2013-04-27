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

import datetime

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

register = template.Library()

def job_status_to_str(value, arg, autoescape=None):
    if value == 0:
        return _("Waiting for rendering to begin...")
    elif value == 1:
        return _("The rendering is in progress...")
    elif value == 2:
        if arg == 'ok':
            return _("Rendering was successful.")
        else:
            return _("Rendering failed! Please contact contact@maposmatic.org for more information.")
    elif value == 3:
        if arg == 'ok':
            return _("Rendering is obsolete: the rendering was successful, but the files are no longer available.")
        else:
            return _("Obsolete failed rendering: the rendering failed, and the incomplete files have been removed.")
    elif value == 4:
        return _("The rendering was cancelled by the user.")

    return ''

def feedparsed(value):
    return datetime.datetime(*value[:6])

register.filter('job_status_to_str', job_status_to_str)
register.filter('feedparsed', feedparsed)
register.filter('abs', lambda x: abs(x))
register.filter('getitem', lambda d,i: d.get(i,''))
