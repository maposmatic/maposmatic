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
import feedparser

from models import MapRenderingJob
import www.settings

def get_latest_blog_posts():
    f = feedparser.parse("http://news.maposmatic.org/?feed=rss2")
    return f.entries[:5]

def all(request):
    # Do not add the useless overhead of parsing blog entries when generating
    # the rss feed
    if request.path == reverse('rss-feed', args=['maps']):
        return {}
    return {
        'randommap': MapRenderingJob.objects.get_random_with_thumbnail(),
        'blogposts': get_latest_blog_posts(),
        'MAPOSMATIC_DAEMON_RUNNING': www.settings.is_daemon_running(),
    }
