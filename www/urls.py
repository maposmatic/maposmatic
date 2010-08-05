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

import maposmatic.feeds
import maposmatic.views
import settings

feeds = {
    'maps': maposmatic.feeds.MapsFeed,
}

urlpatterns = patterns('',
    url(r'^$', maposmatic.views.index,
        name='main'),
    url(r'^about/$', maposmatic.views.about,
        name='about'),

    url(r'^jobs/(?P<job_id>\d+)/(?P<job_nonce>[A-Za-z]{16})$',
        maposmatic.views.job,
        name='job-by-id-and-nonce'),
    url(r'^jobs/(?P<job_id>\d+)$', maposmatic.views.job,
        name='job-by-id'),
    url(r'^jobs/$', maposmatic.views.all_jobs,
        name='jobs'),

    url(r'^maps/$', maposmatic.views.all_maps,
        name='maps'),

    url(r'^new/$', maposmatic.views.new,
        name='new'),

    url(r'^recreate/$', maposmatic.views.recreate,
        name='recreate'),

    url(r'^cancel/$', maposmatic.views.cancel,
        name='cancel'),

    (r'^apis/nominatim/([^/]*/)?(.*)$', maposmatic.views.query_nominatim),

    (r'^apis/papersize', maposmatic.views.query_papersize),

    # Internationalization
    (r'^i18n/', include('django.conf.urls.i18n')),

    # Feeds
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
     {'feed_dict': feeds}),

    # Static data
    (r'^results/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': '/tmp/foo/'}),
    (r'^smedia/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.LOCAL_MEDIA_PATH}),
)
