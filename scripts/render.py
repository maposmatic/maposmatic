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

import Image
import os
import sys

from ocitysmap.coords import BoundingBox
from ocitysmap.street_index import OCitySMap
from www.maposmatic.models import MapRenderingJob
from www.settings import RENDERING_RESULT_PATH, RENDERING_RESULT_FORMATS
from www.settings import OCITYSMAP_CFG_PATH

def render_job(job, prefix=None):
    """Renders the given job, encapsulating all processing errors and
    exceptions.

    This does not affect the job entry in the database in any way. It's the
    responsibility of the caller to do maintain the job status in the database.

    Returns:
        * 0 on success;
        * 1 on ^C;
        * 2 on a rendering exception from OCitySMap.
    """

    if job.administrative_city is None:
        bbox = BoundingBox(job.lat_upper_left, job.lon_upper_left,
                           job.lat_bottom_right, job.lon_bottom_right)
        renderer = OCitySMap(config_file=OCITYSMAP_CFG_PATH,
                             map_areas_prefix=prefix,
                             boundingbox=bbox,
                             language=job.map_language)
    else:
        renderer = OCitySMap(config_file=OCITYSMAP_CFG_PATH,
                             map_areas_prefix=prefix,
                             osmid=job.administrative_osmid,
                             language=job.map_language)

    prefix = os.path.join(RENDERING_RESULT_PATH, job.files_prefix())

    try:
        # Render the map in all RENDERING_RESULT_FORMATS
        result = renderer.render_map_into_files(job.maptitle, prefix,
                                                RENDERING_RESULT_FORMATS,
                                                'zoom:16')

        # Render the index in all RENDERING_RESULT_FORMATS, using the
        # same map size.
        renderer.render_index(job.maptitle, prefix, RENDERING_RESULT_FORMATS,
                              result.width, result.height)

        # Create thumbnail
        if 'png' in RENDERING_RESULT_FORMATS:
            img = Image.open(prefix + '.png')
            img.thumbnail((200, 200), Image.ANTIALIAS)
            img.save(prefix + '_small.png')

        return 0
    except KeyboardInterrupt:
        return 1
    except:
        return 2

if __name__ == '__main__':
    def usage():
        sys.stderr.write('usage: %s <jobid>' % sys.argv[0])

    if len(sys.argv) != 2:
        usage()
        sys.exit(3)

    try:
        jobid = int(sys.argv[1])
        job = MapRenderingJob.objects.get(id=jobid)
        if job:
            sys.exit(render_job(job, 'renderer_%d' % os.getpid()))
        else:
            sys.stderr.write('Job #%d not found!' % jobid)
            sys.exit(4)
    except ValueError:
        usage()
        sys.exit(3)

