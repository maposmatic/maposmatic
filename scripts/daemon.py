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

import logging
import os
import sys
import threading
import time

import render
from www.maposmatic.models import MapRenderingJob
from www.settings import RENDERING_RESULT_PATH, RENDERING_RESULT_MAX_SIZE_GB

_DEFAULT_CLEAN_FREQUENCY = 20       # Clean thread polling frequency, in
                                    # seconds.
_DEFAULT_POLL_FREQUENCY = 10        # Daemon job polling frequency, in seconds

_RESULT_MSGS = {
    render.RESULT_SUCCESS: 'ok',
    render.RESULT_KEYBOARD_INTERRUPT: 'rendering interrupted',
    render.RESULT_PREPARATION_EXCEPTION: 'data preparation failed',
    render.RESULT_RENDERING_EXCEPTION: 'rendering failed',
    render.RESULT_TIMEOUT_REACHED: 'rendering took too long, canceled'
}

l = logging.getLogger('maposmatic')

class MapOSMaticDaemon:
    """
    This is a basic rendering daemon, base class for the different
    implementations of rendering scheduling. By default, it acts as a
    standalone, single-process MapOSMatic rendering daemon.

    It of course uses the TimingOutJobRenderer to ensure no long-lasting job
    stalls the queue.
    """

    def __init__(self, frequency=_DEFAULT_POLL_FREQUENCY):
        self.frequency = frequency
        l.info("MapOSMatic rendering daemon started.")
        self.rollback_orphaned_jobs()

    def rollback_orphaned_jobs(self):
        """Reset all jobs left in the "rendering" state back to the "waiting"
        state to process them correctly."""
        MapRenderingJob.objects.filter(status=1).update(status=0)

    def serve(self):
        """Implement a basic service loop, looking every self.frequency seconds
        for a new job to render and dispatch it if one's available. This method
        can of course be overloaded by subclasses of MapOSMaticDaemon depending
        on their needs."""

        while True:
            try:
                job = MapRenderingJob.objects.to_render()[0]
                self.dispatch(job)
            except IndexError:
                try:
                    time.sleep(self.frequency)
                except KeyboardInterrupt:
                    break

        l.info("MapOSMatic rendering daemon terminating.")

    def dispatch(self, job):
        """In this simple single-process daemon, dispatching is as easy as
        calling the render() method. Subclasses probably want to overload this
        method too and implement a more clever dispatching mechanism.

        Args:
            job (MapRenderingJob): the job to process and render.

        Returns True if the rendering was successful, False otherwise.
        """

        return self.render(job, 'maposmaticd_%d_' % os.getpid())

    def render(self, job, prefix=None):
        """Render a given job. Uses get_renderer() to get the appropriate
        renderer to use to render this job.

        Args:
            job (MapRenderingJob): the job to process and render.
            renderer (JobRenderer): the renderer to use.

        Returns True if the rendering was successful, False otherwise.
        """
        renderer = self.get_renderer(job, prefix)
        job.start_rendering()
        ret = renderer.run()
        job.end_rendering(_RESULT_MSGS[ret])
        return ret == 0

    def get_renderer(self, job, prefix):
        return render.ThreadingJobRenderer(job, prefix=prefix)

class ForkingMapOSMaticDaemon(MapOSMaticDaemon):

    def __init__(self, frequency=_DEFAULT_POLL_FREQUENCY):
        MapOSMaticDaemon.__init__(self, frequency)
        l.info('This is the forking daemon. Will fork to process each job.')

    def get_renderer(self, job, prefix):
        return render.ForkingJobRenderer(job, prefix=prefix)

class RenderingsGarbageCollector(threading.Thread):
    """
    A garbage collector thread that removes old rendering from
    RENDERING_RESULT_PATH when the total size of the directory goes about 80%
    of RENDERING_RESULT_MAX_SIZE_GB.
    """

    def __init__(self, frequency=_DEFAULT_CLEAN_FREQUENCY):
        threading.Thread.__init__(self, name='cleanup')

        self.frequency = frequency
        self.setDaemon(True)

    def run(self):
        """Run the main garbage collector thread loop, cleaning files every
        self.frequency seconds until the program is stopped."""

        l.info("Cleanup thread started.")

        while True:
            self.cleanup()
            time.sleep(self.frequency)

    def get_file_info(self, path):
        """Returns a dictionary of information on the given file.

        Args:
            path (string): the full path to the file.
        Returns a dictionary containing:
            * name: the file base name;
            * path: its full path;
            * size: its size;
            * time: the last time the file contents were changed."""

        s = os.stat(path)
        return {'name': os.path.basename(path),
                'path': path,
                'size': s.st_size,
                'time': s.st_mtime}

    def get_formatted_value(self, value):
        """Returns the given value in bytes formatted for display, with its
        unit."""
        return '%.1f MiB' % (value/1024.0/1024.0)

    def get_formatted_details(self, saved, size, threshold):
        """Returns the given saved space, size and threshold details, formatted
        for display by get_formatted_value()."""

        return 'saved %s, now %s/%s' % \
                (self.get_formatted_value(saved),
                 self.get_formatted_value(size),
                 self.get_formatted_value(threshold))

    def cleanup(self):
        """Run one iteration of the cleanup loop. A sorted list of files from
        the renderings directory is first created, oldest files last. Files are
        then pop()-ed out of the list and removed by cleanup_files() until
        we're back below the size threshold."""

        files = map(lambda f: self.get_file_info(f),
                    [os.path.join(RENDERING_RESULT_PATH, f)
                        for f in os.listdir(RENDERING_RESULT_PATH)
                        if not (f.startswith('.') or
                                f.endswith(render.THUMBNAIL_SUFFIX))])

        # Compute the total size occupied by the renderings, and the actual 80%
        # threshold, in bytes.
        size = reduce(lambda x,y: x+y['size'], files, 0)
        threshold = 0.8 * RENDERING_RESULT_MAX_SIZE_GB * 1024 * 1024 * 1024

        # Stop here if we are below the threshold
        if size < threshold:
            return

        l.info("%s consumed for a %s threshold. Cleaning..." %
               (self.get_formatted_value(size),
                self.get_formatted_value(threshold)))

        # Sort files by timestamp, oldest last, and start removing them by
        # pop()-ing the list.
        files.sort(lambda x,y: cmp(y['time'], x['time']))

        while size > threshold:
            if not len(files):
                l.error("No files to remove and still above threshold! "
                        "Something's wrong!")
                return

            f = files.pop()
            l.debug("Considering file %s..." % f['name'])
            job = MapRenderingJob.objects.get_by_filename(f['name'])
            if job:
                l.debug("Found matching parent job #%d." % job.id)
                removed, saved = job.remove_all_files()
                size -= saved
                if removed:
                    l.info("Removed %d files for job #%d (%s)." %
                           (removed, job.id,
                            self.get_formatted_details(saved, size,
                                                       threshold)))

            else:
                # If we didn't find a parent job, it means this is an orphaned
                # file, we can safely remove it to get back some disk space.
                l.debug("No parent job found.")
                os.remove(f['path'])
                size -= f['size']
                l.info("Removed orphan file %s (%s)." %
                       (f['name'], self.get_formatted_details(f['size'],
                                                              size,
                                                              threshold)))


if __name__ == '__main__':
    if (not os.path.exists(RENDERING_RESULT_PATH)
        or not os.path.isdir(RENDERING_RESULT_PATH)):
        l.error("%s does not exist or is not a directory! "
                  "Please use a valid RENDERING_RESULT_PATH.")
        sys.exit(1)

    try:
        cleaner = RenderingsGarbageCollector()
        daemon = ForkingMapOSMaticDaemon()

        cleaner.start()
        daemon.serve()
    except Exception, e:
        l.exception('Fatal error during daemon execution!')

