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
from django.db import models
from django.utils.translation import ugettext_lazy as _

from datetime import datetime, timedelta
import www.settings
import re
import os

import logging

class MapRenderingJobManager(models.Manager):
    def to_render(self):
        return MapRenderingJob.objects.filter(status=0).order_by('submission_time')

    def queue_size(self):
        return MapRenderingJob.objects.filter(status=0).count()

    # We try to find a rendered map from the last 15 days, which still
    # has its thumbnail present.
    def get_random_with_thumbnail(self):
        fifteen_days_before = datetime.now() - timedelta(15)
        maps = (MapRenderingJob.objects.filter(status=2)
            .filter(submission_time__gte=fifteen_days_before)
            .order_by('?')[0:10])
        for m in maps:
            if m.get_thumbnail():
                return m
        return None

    def get_by_filename(self, name):
        """Tries to find the parent MapRenderingJob of a given file from its
        filename. Both the job ID found in the first part of the prefix and the
        entire files_prefix is used to match a job."""

        try:
            jobid = int(name.split('_', 1)[0])
            job = MapRenderingJob.objects.get(id=jobid)
            if name.startswith(job.files_prefix()):
                return job
        except (ValueError, IndexError, MapRenderingJob.DoesNotExist):
            pass

        return None

SPACE_REDUCE = re.compile(r"\s+")
NONASCII_REMOVE = re.compile(r"[^A-Za-z0-9]+")

class MapRenderingJob(models.Model):

    STATUS_LIST = (
        (0, 'Submitted'),
        (1, 'In progress'),
        (2, 'Done'),
        (3, 'Done w/o files'),
        (4, 'Cancelled'),
        )

    NONCE_SIZE = 16

    maptitle = models.CharField(max_length=256)
    stylesheet = models.CharField(max_length=256)
    layout = models.CharField(max_length=256)
    paper_width_mm = models.IntegerField()
    paper_height_mm = models.IntegerField()

    # When rendering through administrative city is selected, the
    # following three fields must be non empty
    administrative_city = models.CharField(max_length=256, blank=True)
    administrative_osmid = models.IntegerField(blank=True, null=True)

    # When rendering through bounding box is selected, the following
    # four fields must be non empty
    lat_upper_left = models.FloatField(blank=True, null=True)
    lon_upper_left = models.FloatField(blank=True, null=True)
    lat_bottom_right = models.FloatField(blank=True, null=True)
    lon_bottom_right = models.FloatField(blank=True, null=True)

    status = models.IntegerField(choices=STATUS_LIST)
    submission_time = models.DateTimeField(auto_now_add=True)
    startofrendering_time = models.DateTimeField(null=True)
    endofrendering_time = models.DateTimeField(null=True)
    resultmsg = models.CharField(max_length=256, null=True)
    submitterip = models.IPAddressField()
    index_queue_at_submission = models.IntegerField()
    map_language = models.CharField(max_length=16)

    nonce = models.CharField(max_length=NONCE_SIZE, blank=True)

    objects = MapRenderingJobManager()

    def __str__(self):
        return self.maptitle.encode('utf-8')

    def maptitle_computized(self):
        t = self.maptitle.strip()
        t = SPACE_REDUCE.sub("-", t)
        t = NONASCII_REMOVE.sub("", t)
        return t

    def files_prefix(self):
        return "%06d_%s_%s" % (self.id,
                             self.startofrendering_time.strftime("%Y-%m-%d_%H-%M"),
                             self.maptitle_computized())


    def start_rendering(self):
        self.status = 1
        self.startofrendering_time = datetime.now()
        self.save()

    def end_rendering(self, resultmsg):
        self.status = 2
        self.endofrendering_time = datetime.now()
        self.resultmsg = resultmsg
        self.save()

    def rendering_time_gt_1min(self):
        if self.needs_waiting():
            return False

        delta = self.endofrendering_time - self.startofrendering_time
        return delta.seconds > 60

    def __is_ok(self):              return self.resultmsg == 'ok'

    def is_waiting(self):           return self.status == 0
    def is_rendering(self):         return self.status == 1
    def needs_waiting(self):        return self.status  < 2

    def is_done(self):              return self.status == 2
    def is_done_ok(self):           return self.is_done() and self.__is_ok()
    def is_done_failed(self):       return self.is_done() and not self.__is_ok()

    def is_obsolete(self):          return self.status == 3
    def is_obsolete_ok(self):       return self.is_obsolete() and self.__is_ok()
    def is_obsolete_failed(self):   return self.is_obsolete() and not self.__is_ok()

    def is_cancelled(self):         return self.status == 4

    def get_map_fileurl(self, format):
        return www.settings.RENDERING_RESULT_URL + "/" + self.files_prefix() + "." + format

    def get_map_filepath(self, format):
        return os.path.join(www.settings.RENDERING_RESULT_PATH, self.files_prefix() + "." + format)

    def output_files(self):
        """Returns a structured dictionary of the output files for this job.
        The result contains two lists, 'maps' and 'indeces', listing the output
        files. Each file is reported by a tuple (format, path, title, size)."""

        allfiles = {'maps': [], 'indeces': []}

        for format in www.settings.RENDERING_RESULT_FORMATS:
            map_path = self.get_map_filepath(format)
            if format != 'csv' and os.path.exists(map_path):
                # Map files (all formats but CSV)
                allfiles['maps'].append((format, self.get_map_fileurl(format),
                    _("%(title)s %(format)s Map") % {'title': self.maptitle,
                                                     'format': format.upper()},
                    os.stat(map_path).st_size, map_path))
            elif format == 'csv' and os.path.exists(map_path):
                # Index CSV file
                allfiles['indeces'].append(
                    (format, self.get_map_fileurl(format),
                     _("%(title)s %(format)s Index") % {'title': self.maptitle,
                                                       'format': format.upper()},
                    os.stat(map_path).st_size, map_path))

        return allfiles

    def has_output_files(self):
        """This function tells whether this job still has its output files
        available on the rendering storage.

        Their actual presence is checked if the job is considered done and not
        yet obsolete."""

        if self.is_done():
            files = self.output_files()
            return len(files['maps']) + len(files['indeces'])

        return False

    def remove_all_files(self):
        """Removes all the output files from this job, and returns the space
        saved in bytes (Note: the thumbnail is not removed)."""

        files = self.output_files()
        saved = 0
        removed = 0

        for f in (files['maps'] + files['indeces']):
            try:
                os.remove(f[4])
                removed += 1
                saved += f[3]
            except OSError:
                pass

        self.status = 3
        self.save()
        return removed, saved

    def cancel(self):
        self.status = 4
        self.endofrendering_time = datetime.now()
        self.resultmsg = 'rendering cancelled'
        self.save()

    def get_thumbnail(self):
        thumbnail_file = os.path.join(www.settings.RENDERING_RESULT_PATH, self.files_prefix() + "_small.png")
        thumbnail_url = www.settings.RENDERING_RESULT_URL + "/" + self.files_prefix() + "_small.png"
        if os.path.exists(thumbnail_file):
            return thumbnail_url
        else:
            return None

    def current_position_in_queue(self):
        return MapRenderingJob.objects.filter(status=0).filter(id__lte=self.id).count()

    # Estimate the date at which the rendering will be started
    def rendering_estimated_start_time(self):
        waiting_time = datetime.now() - self.submission_time
        progression = self.index_queue_at_submission - self.current_position_in_queue()
        if progression == 0:
            return datetime.now()
        mean_job_rendering_time = waiting_time // progression
        estimated_time_left = mean_job_rendering_time * self.current_position_in_queue()
        return datetime.now() + estimated_time_left

    def get_absolute_url(self):
        return reverse('job-by-id', args=[self.id])

