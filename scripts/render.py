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

import ctypes
import Image
import logging
import os
import sys
import threading
import subprocess

import ocitysmap2
import ocitysmap2.coords
from ocitysmap2 import renderers
from www.maposmatic.models import MapRenderingJob
from www.settings import OCITYSMAP_CFG_PATH
from www.settings import RENDERING_RESULT_PATH, RENDERING_RESULT_FORMATS

RESULT_SUCCESS = 0
RESULT_KEYBOARD_INTERRUPT = 1
RESULT_PREPARATION_EXCEPTION = 2
RESULT_RENDERING_EXCEPTION = 3
RESULT_TIMEOUT_REACHED = 4

THUMBNAIL_SUFFIX = '_small.png'

l = logging.getLogger('maposmatic')

class TimingOutJobRenderer:
    """
    The TimingOutJobRenderer is a wrapper around JobRenderer implementing
    timeout management. It uses JobRenderer as a thread, and tries to join it
    for the given timeout. If the timeout is reached, the thread is suspended,
    cleaned up and killed.

    The TimingOutJobRenderer has exactly the same API as the non-threading
    JobRenderer, so it can be used in place of JobRenderer very easily.
    """

    def __init__(self, job, timeout=1200, prefix=None):
        """Initializes this TimingOutJobRenderer with a given job and a timeout.

        Args:
            job (MapRenderingJob): the job to render.
            timeout (int): a timeout, in seconds (defaults to 20 minutes).
            prefix (string): renderer map_areas table prefix.
        """

        self.__timeout = timeout
        self.__thread = JobRenderer(job, prefix)

    def run(self):
        """Renders the job using a JobRendered, encapsulating all processing
        errors and exceptions, with the addition here of a processing timeout.

        Returns one of the RESULT_ constants.
        """

        self.__thread.start()
        self.__thread.join(self.__timeout)

        # If the thread is no longer alive, the timeout was not reached and all
        # is well.
        if not self.__thread.isAlive():
            return self.__thread.result

        l.info("Rendering of job #%d took too long (timeout reached)!" %
               self.__thread.job.id)

        # Remove the job files
        self.__thread.job.remove_all_files()

        # Kill the thread and return TIMEOUT_REACHED
        self.__thread.kill()
        del self.__thread

        l.debug("Thread removed.")
        return RESULT_TIMEOUT_REACHED

class JobRenderer(threading.Thread):
    """
    A simple, blocking job rendered. It can be used as a thread, or directly in
    the main processing path of the caller if it chooses to call run()
    directly.
    """

    def __init__(self, job, prefix):
        threading.Thread.__init__(self, name='renderer')
        self.job = job
        self.prefix = prefix
        self.result = None

    def __get_my_tid(self):
        if not self.isAlive():
            raise threading.ThreadError("the thread is not active")

        # Do we have it cached?
        if hasattr(self, '__thread_id'):
            return self.__thread_id

        # If not, look for it
        for tid, tobj in threading._active.items():
            if tobj is self:
                self.__thread_id = tid
                return self.__thread_id

        raise AssertionError("Could not resolve the thread's ID")

    def kill(self):
        l.debug("Killing job #%d's worker thread..." % self.job.id)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.__get_my_tid(),
                ctypes.py_object(SystemExit))
        if res == 0:
            raise ValueError("Invalid thread ID")
        elif res != 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.__get_my_tid(), 0)
            raise SystemError("PyThreadState_SetAsync failed")

    def _gen_thumbnail(self, prefix, paper_width_mm, paper_height_mm):
        l.info('Creating map thumbnail...')
        if self.job.layout == "multi_page":
            # Depending on whether we're rendering landscape or
            # portrait, adapt how the tiling is done.
            if paper_width_mm > paper_height_mm:
                tile = "1x2"
            else:
                tile = "2x1"

            # With the 'montage' command from ImageMagick, create an
            # image with the first two pages of the PDF (cover page
            # and overview page).
            montage_cmd = [ "montage", "-tile", tile, "%s.pdf[0]" % prefix,
                            "%s.pdf[2]" % prefix, "-geometry", "+10+10",
                            "-shadow", "%s%s" % (prefix, THUMBNAIL_SUFFIX) ]
            ret = subprocess.call(montage_cmd)
            if ret != 0:
                return

            # And now scale it to the normal thumbnail size
            mogrify_cmd = [ "mogrify", "-scale", "200x200",
                            "%s%s" % (prefix, THUMBNAIL_SUFFIX) ]
            ret = subprocess.call(mogrify_cmd)
            if ret != 0:
                return
        else:
            if 'png' in RENDERING_RESULT_FORMATS:
                img = Image.open(prefix + '.png')
                img.thumbnail((200, 200), Image.ANTIALIAS)
                img.save(prefix + THUMBNAIL_SUFFIX)

    def run(self):
        """Renders the given job, encapsulating all processing errors and
        exceptions.

        This does not affect the job entry in the database in any way. It's the
        responsibility of the caller to do maintain the job status in the
        database.

        Returns one of the RESULT_ constants.
        """

        l.info("Rendering job #%d '%s'..." % (self.job.id, self.job.maptitle))

        try:
            renderer = ocitysmap2.OCitySMap(OCITYSMAP_CFG_PATH)
            config = ocitysmap2.RenderingConfiguration()
            config.title = self.job.maptitle
            config.osmid = self.job.administrative_osmid

            if config.osmid:
                bbox_wkt, area_wkt \
                    = renderer.get_geographic_info(config.osmid)
                config.bounding_box = ocitysmap2.coords.BoundingBox.parse_wkt(
                    bbox_wkt)
            else:
                config.bounding_box = ocitysmap2.coords.BoundingBox(
                        self.job.lat_upper_left,
                        self.job.lon_upper_left,
                        self.job.lat_bottom_right,
                        self.job.lon_bottom_right)

            config.language = self.job.map_language
            config.stylesheet = renderer.get_stylesheet_by_name(
                self.job.stylesheet)
            config.paper_width_mm = self.job.paper_width_mm
            config.paper_height_mm = self.job.paper_height_mm
        except KeyboardInterrupt:
            self.result = RESULT_KEYBOARD_INTERRUPT
            l.info("Rendering of job #%d interrupted!" % self.job.id)
            return self.result
        except Exception, e:
            self.result = RESULT_PREPARATION_EXCEPTION
            l.exception("Rendering of job #%d failed (exception occurred during"
                        " data preparation)!" % self.job.id)
            return self.result

        prefix = os.path.join(RENDERING_RESULT_PATH, self.job.files_prefix())

        try:
            # Get the list of output formats (PNG, PDF, SVGZ, CSV)
            # that the renderer accepts.
            renderer_cls = renderers.get_renderer_class_by_name(self.job.layout)
            compatible_output_formats = renderer_cls.get_compatible_output_formats()

            # Compute the intersection of the accepted output formats
            # with the desired output formats.
            output_formats = \
                list(set(compatible_output_formats) & set(RENDERING_RESULT_FORMATS))

            renderer.render(config, self.job.layout,
                            output_formats, prefix)

            # Create thumbnail
            self._gen_thumbnail(prefix, config.paper_width_mm,
                                config.paper_height_mm)

            self.result = RESULT_SUCCESS
            l.info("Finished rendering of job #%d." % self.job.id)
        except KeyboardInterrupt:
            self.result = RESULT_KEYBOARD_INTERRUPT
            l.info("Rendering of job #%d interrupted!" % self.job.id)
        except Exception, e:
            self.result = RESULT_RENDERING_EXCEPTION
            l.exception("Rendering of job #%d failed (exception occurred during"
                        " rendering)!" % self.job.id)

        # Remove the job files if the rendering was not successful.
        if self.result:
            self.job.remove_all_files()

        return self.result


if __name__ == '__main__':
    def usage():
        sys.stderr.write('usage: %s <jobid> [timeout]\n' % sys.argv[0])

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        usage()
        sys.exit(3)

    try:
        jobid = int(sys.argv[1])
        job = MapRenderingJob.objects.get(id=jobid)

        if job:
            prefix = 'renderer_%d_' % os.getpid()
            if len(sys.argv) == 3:
                renderer = TimingOutJobRenderer(job, int(sys.argv[2]), prefix)
            else:
                renderer = JobRenderer(job, prefix)

            sys.exit(renderer.run())
        else:
            sys.stderr.write('Job #%d not found!' % jobid)
            sys.exit(4)
    except ValueError:
        usage()
        sys.exit(3)

