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

import django
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import maposmatic.feeds
import maposmatic.views
import settings

urlpatterns = patterns('',
    url(r'^$',
        maposmatic.views.index,
        name='main'),

    url(r'^new/$',
        maposmatic.views.new,
        name='new'),
    url(r'^recreate/$',
        maposmatic.views.recreate,
        name='recreate'),
    url(r'^cancel/$',
        maposmatic.views.cancel,
        name='cancel'),

    url(r'^maps/(?P<id>\d+)/(?P<nonce>[A-Za-z]{16})$',
        maposmatic.views.map_full,
        name='map-by-id-and-nonce'),
    url(r'^maps/(?P<id>\d+)$',
        maposmatic.views.map_full,
        name='map-by-id'),
    url(r'^maps/$',
        maposmatic.views.maps,
        name='maps'),

    url(r'^about/$',
        maposmatic.views.about,
        name='about'),
    url(r'^donate/$',
        maposmatic.views.donate,
        name='donate'),
    url(r'^donate-thanks/$',
        maposmatic.views.donate_thanks,
        name='donate-thanks'),

    (r'^apis/nominatim/$', maposmatic.views.api_nominatim),
    (r'^apis/reversegeo/([^/]*)/([^/]*)/$', maposmatic.views.api_nominatim_reverse),
    (r'^apis/papersize', maposmatic.views.api_papersize),
    (r'^apis/boundingbox/([^/]*)/$', maposmatic.views.api_bbox),

    # Feeds
    django.VERSION[1] >= 4 and \
        url(r'^feeds/maps/', maposmatic.feeds.MapsFeed(),
            name='rss-feed') or \
        url(r'^feeds/(?P<url>.*)/$',
            'django.contrib.syndication.views.feed',
            {'feed_dict': {'maps': maposmatic.feeds.MapsFeed}},
            name='rss-feed'),

    # Internationalization
    (r'^i18n/', include('django.conf.urls.i18n')),
)

if settings.DEBUG:
    urlpatterns.extend(patterns('',
        (r'^results/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.RENDERING_RESULT_PATH}),

        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.LOCAL_MEDIA_PATH}),
    ))
