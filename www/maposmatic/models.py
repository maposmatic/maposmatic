from django.db import models
from datetime import datetime
import re

import logging

class MapRenderingJobManager(models.Manager):
    def to_render(self):
        return MapRenderingJob.objects.filter(status=0).order_by('submission_time')

    def queue_size(self):
        return MapRenderingJob.objects.filter(status=0).count()

SPACE_REDUCE = re.compile(r"\s+")
NONASCII_REMOVE = re.compile(r"[^A-Za-z0-9]+")

class MapRenderingJob(models.Model):

    STATUS_LIST = (
        (0, 'Submitted'),
        (1, 'In progress'),
        (2, 'Done'),
        )

    maptitle = models.CharField(max_length=256)
    administrative_city = models.CharField(max_length=256, blank=True, null=True)
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

    objects = MapRenderingJobManager()

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

    def current_position_in_queue(self):
        return MapRenderingJob.objects.filter(status=0).filter(index_queue_at_submission__lte=self.index_queue_at_submission).count()

    # Estimate the date at which the rendering will be started
    def rendering_estimated_start_time(self):
        waiting_time = datetime.now() - self.submission_time
        progression = self.index_queue_at_submission - self.current_position_in_queue()
        if progression == 0:
            return datetime.now()
        mean_job_rendering_time = waiting_time // progression
        estimated_time_left = mean_job_rendering_time * self.current_position_in_queue()
        return datetime.now() + estimated_time_left
