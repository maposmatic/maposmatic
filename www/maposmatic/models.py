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
        maps = MapRenderingJob.objects.filter(status=2).filter(submission_time__gte=fifteen_days_before).order_by('?')[0:10]
        for m in maps:
            if m.get_thumbnail():
                return m
        return None

SPACE_REDUCE = re.compile(r"\s+")
NONASCII_REMOVE = re.compile(r"[^A-Za-z0-9]+")

class MapRenderingJob(models.Model):

    STATUS_LIST = (
        (0, 'Submitted'),
        (1, 'In progress'),
        (2, 'Done'),
        )

    maptitle = models.CharField(max_length=256)

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

    def is_waiting(self):
        return self.status == 0

    def is_rendering(self):
        return self.status == 1

    def is_done(self):
        return self.status == 2

    def is_done_ok(self):
        return self.is_done() and self.resultmsg == "ok"

    def is_done_failed(self):
        return self.is_done() and self.resultmsg != "ok"

    def get_map_fileurl(self, format):
        return www.settings.RENDERING_RESULT_URL + "/" + self.files_prefix() + "." + format

    def get_map_filepath(self, format):
        return os.path.join(www.settings.RENDERING_RESULT_PATH, self.files_prefix() + "." + format)

    def get_index_fileurl(self, format):
        return www.settings.RENDERING_RESULT_URL + "/" + self.files_prefix() + "_index." + format

    def get_index_filepath(self, format):
        return os.path.join(www.settings.RENDERING_RESULT_PATH, self.files_prefix() + "_index." + format)

    def output_files(self):
        allfiles = {'maps': [], 'indeces': []}

        for format in www.settings.RENDERING_RESULT_FORMATS:
            # Map files (all formats but CSV)
            if format != 'csv' and os.path.exists(self.get_map_filepath(format)):
                allfiles['maps'].append((format, self.get_map_fileurl(format),
                    _("%(title)s %(format)s Map") % {'title': self.maptitle, 'format': format.upper()},
                    os.stat(self.get_map_filepath(format)).st_size))
            # Index files
            if os.path.exists(self.get_index_filepath(format)):
                allfiles['indeces'].append((format, self.get_index_fileurl(format),
                    _("%(title)s %(format)s Index") % {'title': self.maptitle, 'format': format.upper()},
                    os.stat(self.get_index_filepath(format)).st_size))

        return allfiles

    def has_output_files(self):
        files = self.output_files()
        return len(files['maps']) + len(files['indeces'])

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
