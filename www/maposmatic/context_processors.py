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

from django.core.urlresolvers import reverse
import django.utils.translation
import feedparser
import datetime

from models import MapRenderingJob
import www.settings

from www.maposmatic import gisdb
import psycopg2

def get_latest_blog_posts():
    f = feedparser.parse("http://news.maposmatic.org/?feed=rss2")
    return f.entries[:5]

def get_osm_database_last_update():
    try:
        with open(www.settings.GIS_DATABASE_LAG_FILE) as f:
            try:
                return datetime.datetime.strptime(
                    '%s' % f.read().strip(),
                    '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
    except IOError:
        pass

    return None

def all(request):
    # Do not add the useless overhead of parsing blog entries when generating
    # the rss feed
    if request.path == reverse('rss-feed', args=['maps']):
        return {}

    l = django.utils.translation.get_language()
    if www.settings.PAYPAL_LANGUAGES.has_key(l):
        paypal_lang_code = www.settings.PAYPAL_LANGUAGES[l][0]
        paypal_country_code = www.settings.PAYPAL_LANGUAGES[l][1]
    else:
        paypal_lang_code = "en_US"
        paypal_country_code = "US"

    return {
        'randommap': MapRenderingJob.objects.get_random_with_thumbnail(),
        'blogposts': get_latest_blog_posts(),
        'MAPOSMATIC_DAEMON_RUNNING': www.settings.is_daemon_running(),
        'osm_date': get_osm_database_last_update(),
        'utc_now': datetime.datetime.utcnow(),
        'DEBUG': www.settings.DEBUG,
        'paypal_lang_code': paypal_lang_code,
        'paypal_country_code': paypal_country_code,
    }
