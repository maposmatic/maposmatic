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

# Create your views here.

from django.core.paginator import Paginator
from django.forms.util import ErrorList
from django.forms import CharField, ChoiceField, FloatField, RadioSelect, \
                         ModelForm, ValidationError
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.template import RequestContext

from www.maposmatic.models import MapRenderingJob
import datetime
import psycopg2
import www.settings
import math
from www.maposmatic.widgets import AreaField
from ocitysmap.coords import BoundingBox as OCMBoundingBox

# Test if a given city has its administrative boundaries inside the
# OpenStreetMap database. We don't go through the Django ORM but
# directly to the database for simplicity reasons.
def city_exists(city):

    # If not GIS database is configured, bypass the city_exists check by
    # returning True.
    if not www.settings.has_gis_database():
        return True

    try:
        conn = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" %
                                (www.settings.GIS_DATABASE_NAME,
                                 www.settings.DATABASE_USER,
                                 www.settings.DATABASE_HOST,
                                 www.settings.DATABASE_PASSWORD))
    except psycopg2.OperationalError:
        return False

    cursor = conn.cursor()
    cursor.execute("""select count(*) from planet_osm_line where
                        boundary='administrative' and
                        admin_level='8' and
                        name=%s""",
                   (city,))
    result = cursor.fetchall()
    return (result[0][0] == 1)

class MapRenderingJobForm(ModelForm):
    class Meta:
        model = MapRenderingJob
        fields = ('maptitle', 'administrative_city', 'lat_upper_left',
                  'lon_upper_left', 'lat_bottom_right', 'lon_bottom_right')

    modes = (('admin', _('Administrative boundary')),
             ('bbox', _('Bounding box')))
    mode = ChoiceField(choices=modes, initial='admin', widget=RadioSelect)
    maptitle = CharField(max_length=256, required=False)
    bbox = AreaField(label=_("Area"), fields=(FloatField(), FloatField(),
                                              FloatField(), FloatField()))

    def clean(self):
        cleaned_data = self.cleaned_data

        mode = cleaned_data.get("mode")
        city = cleaned_data.get("administrative_city")
        title = cleaned_data.get("maptitle")

        if mode == 'admin':
            if city == "":
                msg = _(u"Administrative city required")
                self._errors["administrative_city"] = ErrorList([msg])
                del cleaned_data["administrative_city"]
            elif not city_exists(city):
                msg = _(u"No administrative boundaries found for this city. Try with proper casing.")
                self._errors["administrative_city"] = ErrorList([msg])
                del cleaned_data["administrative_city"]

            # No choice, the map title is always the name of the city
            cleaned_data["maptitle"] = city

            # Make sure that bbox and admin modes are exclusive
            cleaned_data["lat_upper_left"] = None
            cleaned_data["lon_upper_left"] = None
            cleaned_data["lat_bottom_right"] = None
            cleaned_data["lon_bottom_right"] = None

        if mode == 'bbox':
            if title == '':
                msg = _(u"Map title required")
                self._errors["maptitle"] = ErrorList([msg])
                del cleaned_data["maptitle"]

            for f in [ "lat_upper_left", "lon_upper_left",
                       "lat_bottom_right", "lon_bottom_right" ]:
                val = cleaned_data.get(f)
                if val is None:
                    msg = _(u"Required")
                    self._errors[f] = ErrorList([msg])
                    del cleaned_data[f]

            lat_upper_left = cleaned_data.get("lat_upper_left")
            lon_upper_left = cleaned_data.get("lon_upper_left")
            lat_bottom_right = cleaned_data.get("lat_bottom_right")
            lon_bottom_right = cleaned_data.get("lon_bottom_right")

            boundingbox = OCMBoundingBox(lat_upper_left,
                                         lon_upper_left,
                                         lat_bottom_right,
                                         lon_bottom_right)
            (metric_size_lat, metric_size_long) = boundingbox.spheric_sizes()
            if metric_size_lat > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS or \
                    metric_size_long > www.settings.BBOX_MAXIMUM_LENGTH_IN_METERS:
                msg = _(u"Bounding Box too big")
                self._errors['bbox'] = ErrorList([msg])

            if (lat_upper_left > 51.956 or
                lon_upper_left < -7.838 or
                lat_bottom_right < 41.458 or
                lon_bottom_right > 11.937):
                msg = _(u"Sorry, only cities in France can be rendered for the moment")
                self._errors['bbox'] = ErrorList([msg])

            # Make sure that bbox and admin modes are exclusive
            cleaned_data["administrative_city"] = ''

        return cleaned_data

def rendering_already_exists(city):
    # First try to find rendered items
    rendered_items = (MapRenderingJob.objects.
                      filter(administrative_city=city).
                      filter(status=2).filter(resultmsg="ok").order_by("-submission_time")[:1])

    if len(rendered_items):
        rendered_item = rendered_items[0]
        if rendered_item.output_files() != []:
            return '/jobs/%d' % rendered_item.id

    # Then try to find items being rendered or waiting for rendering
    rendered_items = (MapRenderingJob.objects.
                      filter(administrative_city=city).
                      filter(status__in=[0,1]).
                      order_by("-submission_time")[:1])

    if len(rendered_items):
        rendered_item = rendered_items[0]
        return '/jobs/%d' % rendered_item.id

    return None

def index(request):
    if request.method == 'POST':
        form = MapRenderingJobForm(request.POST)
        if form.is_valid():
            job = MapRenderingJob()
            job.maptitle = form.cleaned_data['maptitle']
            job.administrative_city = form.cleaned_data['administrative_city']

            if job.administrative_city:
                url = rendering_already_exists(job.administrative_city)
                if url:
                    return HttpResponseRedirect(url)

            job.lat_upper_left = form.cleaned_data['lat_upper_left']
            job.lon_upper_left = form.cleaned_data['lon_upper_left']
            job.lat_bottom_right = form.cleaned_data['lat_bottom_right']
            job.lon_bottom_right = form.cleaned_data['lon_bottom_right']
            job.status = 0 # Submitted
            job.submitterip = request.META['REMOTE_ADDR']
            job.index_queue_at_submission = MapRenderingJob.objects.queue_size()
            job.save()

            return HttpResponseRedirect('/jobs/%d' % job.id)
    else:
        form = MapRenderingJobForm()
    return render_to_response('maposmatic/index.html',
                              { 'form' : form },
                              context_instance=RequestContext(request))

def job(request, job_id):
    job = get_object_or_404(MapRenderingJob, id=job_id)
    return render_to_response('maposmatic/job.html',
                              { 'job' : job },
                              context_instance=RequestContext(request))

def all_jobs(request):
    one_day_before = datetime.datetime.now() - datetime.timedelta(1)
    job_list = (MapRenderingJob.objects.all()
            .order_by('-submission_time')
            .filter(submission_time__gte=one_day_before))
    paginator = Paginator(job_list, www.settings.ITEMS_PER_PAGE)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        jobs = paginator.page(page)
    except (EmptyPage, InvalidPage):
        jobs = paginator.page(paginator.num_pages)

    return render_to_response('maposmatic/all_jobs.html',
                              { 'jobs' : jobs },
                              context_instance=RequestContext(request))

def all_maps(request):
    map_list = (MapRenderingJob.objects.filter(status=2)
            .filter(resultmsg="ok")
            .order_by("-submission_time"))
    paginator = Paginator(map_list, www.settings.ITEMS_PER_PAGE)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        maps = paginator.page(page)
    except (EmptyPage, InvalidPage):
        maps = paginator.page(paginator.num_pages)
    return render_to_response('maposmatic/all_maps.html',
                              { 'maps': maps },
                              context_instance=RequestContext(request))

def about(request):
    return render_to_response('maposmatic/about.html',
                              context_instance=RequestContext(request))
