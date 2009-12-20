#!/usr/bin/python
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

from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import maposmatic.views
import settings

urlpatterns = patterns('',
    (r'^$', maposmatic.views.index),
    (r'^smedia/(?P<path>.*)$',
     'django.views.static.serve',
     {'document_root': settings.LOCAL_MEDIA_PATH}),
    (r'^jobs/(?P<job_id>\d+)$', maposmatic.views.job),
    (r'^jobs/$', maposmatic.views.all_jobs),
    (r'^maps/$', maposmatic.views.all_maps),
    (r'^about/$', maposmatic.views.about),
    (r'^nominatim/([^/]*/)?(.*)$', maposmatic.views.query_nominatim),
    (r'^i18n/', include('django.conf.urls.i18n')),

    (r'^results/(?P<path>.*)$',
     'django.views.static.serve',
     {'document_root': '/tmp/foo/'}),

)
