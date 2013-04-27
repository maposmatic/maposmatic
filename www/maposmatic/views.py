# coding: utf-8

# maposmatic, the web front-end of the MapOSMatic city map generation system
# Copyright (C) 2009  David Decotigny
# Copyright (C) 2009  Frédéric Lehobey
# Copyright (C) 2009  Pierre Mauduit
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

# Views for MapOSMatic

import datetime
import logging

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

import ocitysmap
from www.maposmatic import helpers, forms, nominatim, models
import www.settings

LOG = logging.getLogger('maposmatic')

try:
    from json import dumps as json_encode
except ImportError:
    try:
        from cjson import encode as json_encode
    except ImportError:
        from json import write as json_encode

def index(request):
    """The main page."""
    form = forms.MapSearchForm(request.GET)

    job_list = (models.MapRenderingJob.objects.all()
                .order_by('-submission_time'))
    job_list = (job_list.filter(status=0) |
                job_list.filter(status=1))

    return render_to_response('maposmatic/index.html',
                              { 'form': form,
                                'queued': job_list.count()
                              },
                              context_instance=RequestContext(request))

def about(request):
    """The about page."""
    return render_to_response('maposmatic/about.html',
                              context_instance=RequestContext(request))

def donate(request):
    """The donate page."""
    return render_to_response('maposmatic/donate.html',
                              context_instance=RequestContext(request))

def donate_thanks(request):
    """The thanks for donation page."""
    return render_to_response('maposmatic/donate-thanks.html',
                              context_instance=RequestContext(request))

def new(request):
    """The map creation page and form."""

    if request.method == 'POST':
        form = forms.MapRenderingJobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.administrative_osmid = form.cleaned_data.get('administrative_osmid')
            job.stylesheet = form.cleaned_data.get('stylesheet')
            job.layout = form.cleaned_data.get('layout')
            job.paper_width_mm = form.cleaned_data.get('paper_width_mm')
            job.paper_height_mm = form.cleaned_data.get('paper_height_mm')
            job.status = 0 # Submitted
            job.submitterip = request.META['REMOTE_ADDR']
            job.map_language = form.cleaned_data.get('map_language')
            job.index_queue_at_submission = (models.MapRenderingJob.objects
                                             .queue_size())
            job.nonce = helpers.generate_nonce(models.MapRenderingJob.NONCE_SIZE)
            job.save()

            return HttpResponseRedirect(reverse('map-by-id-and-nonce',
                                                args=[job.id, job.nonce]))
    else:
        form = forms.MapRenderingJobForm()

    return render_to_response('maposmatic/new.html',
                              { 'form' : form },
                              context_instance=RequestContext(request))

def map_full(request, id, nonce=None):
    """The full-page map details page.

    Args:
        id (int): the job ID in the database.
    """

    job = get_object_or_404(models.MapRenderingJob, id=id)
    isredirected = request.session.get('redirected', False)
    request.session.pop('redirected', None)

    queue_size = models.MapRenderingJob.objects.queue_size()
    progress = 100
    if queue_size:
        progress = 20 + int(80 * (queue_size -
            job.current_position_in_queue()) / float(queue_size))

    refresh = job.is_rendering() and \
        www.settings.REFRESH_JOB_RENDERING or \
        www.settings.REFRESH_JOB_WAITING

    return render_to_response('maposmatic/map-full.html',
                              { 'map': job, 'redirected': isredirected,
                                'nonce': nonce, 'refresh': refresh,
                                'progress': progress, 'queue_size': queue_size },
                              context_instance=RequestContext(request))

def maps(request):
    """Displays all maps and jobs, sorted by submission time, or maps matching
    the search terms when provided."""

    map_list = None

    form = forms.MapSearchForm(request.GET)
    if form.is_valid():
        map_list = (models.MapRenderingJob.objects
                    .order_by('-submission_time')
                    .filter(maptitle__icontains=form.cleaned_data['query']))
        if len(map_list) == 1:
            return HttpResponseRedirect(reverse('map-by-id',
                                                args=[map_list[0].id]))
    else:
        form = forms.MapSearchForm()

    if map_list is None:
        map_list = (models.MapRenderingJob.objects
                    .order_by('-submission_time'))

    paginator = Paginator(map_list, www.settings.ITEMS_PER_PAGE)

    try:
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        maps = paginator.page(page)
    except (EmptyPage, InvalidPage):
        maps = paginator.page(paginator.num_pages)

    return render_to_response('maposmatic/maps.html',
                              { 'maps': maps, 'form': form,
                                'is_search': form.is_valid(),
                                'pages': helpers.get_pages_list(maps, paginator) },
                              context_instance=RequestContext(request))


def recreate(request):
    if request.method == 'POST':
        form = forms.MapRecreateForm(request.POST)
        if form.is_valid():
            job = get_object_or_404(models.MapRenderingJob,
                                    id=form.cleaned_data['id'])

            newjob = models.MapRenderingJob()
            newjob.maptitle = job.maptitle

            newjob.administrative_city = job.administrative_city
            newjob.administrative_osmid = job.administrative_osmid

            newjob.lat_upper_left = job.lat_upper_left
            newjob.lon_upper_left = job.lon_upper_left
            newjob.lat_bottom_right = job.lat_bottom_right
            newjob.lon_bottom_right = job.lon_bottom_right

            newjob.stylesheet = job.stylesheet
            newjob.layout = job.layout
            newjob.paper_width_mm = job.paper_width_mm
            newjob.paper_height_mm = job.paper_height_mm

            newjob.status = 0 # Submitted
            newjob.submitterip = request.META['REMOTE_ADDR']
            newjob.map_language = job.map_language
            newjob.index_queue_at_submission = (models.MapRenderingJob.objects
                                               .queue_size())
            newjob.nonce = helpers.generate_nonce(models.MapRenderingJob.NONCE_SIZE)
            newjob.save()

            return HttpResponseRedirect(reverse('map-by-id-and-nonce',
                                                args=[newjob.id, newjob.nonce]))

    return HttpResponseBadRequest("ERROR: Invalid request")

def cancel(request):
    if request.method == 'POST':
        form = forms.MapCancelForm(request.POST)
        if form.is_valid():
            job = get_object_or_404(models.MapRenderingJob,
                                    id=form.cleaned_data['id'],
                                    nonce=form.cleaned_data['nonce'])
            job.cancel()

            return HttpResponseRedirect(reverse('map-by-id-and-nonce',
                                                args=[job.id, job.nonce]))

    return HttpResponseBadRequest("ERROR: Invalid request")

def api_nominatim(request):
    """Nominatim query gateway."""
    exclude = request.GET.get('exclude', '')
    squery = request.GET.get('q', '')
    lang = None

    if 'HTTP_ACCEPT_LANGUAGE' in request.META:
        # Accept-Language headers typically look like
        # fr,fr-fr;q=0.8,en-us;q=0.5,en;q=0.3. Unfortunately,
        # Nominatim behaves improperly with such a string: it gives
        # the region name in French, but the country name in
        # English. We split at the first comma to only keep the
        # preferred language, which makes Nominatim work properly.
        lang = request.META['HTTP_ACCEPT_LANGUAGE'].split(',')[0]

    try:
        contents = nominatim.query(squery, exclude, with_polygons=False,
                accept_language=lang)
    except Exception, e:
        LOG.exception("Error querying Nominatim")
        contents = []

    return HttpResponse(content=json_encode(contents),
                        mimetype='text/json')

def api_nominatim_reverse(request, lat, lon):
    """Nominatim reverse geocoding query gateway."""
    lat = float(lat)
    lon = float(lon)
    return HttpResponse(json_encode(nominatim.reverse_geo(lat, lon)),
                        mimetype='text/json')

def api_papersize(request):
    """API handler to get the compatible paper sizes for the provided layout
    and bounding box."""

    if request.method != 'POST':
        return HttpResponseBadRequest("ERROR: Bad request")

    f = forms.MapPaperSizeForm(request.POST)
    if not f.is_valid():
       return HttpResponseBadRequest("ERROR: Invalid arguments")

    renderer = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)
    osmid = f.cleaned_data.get('osmid')
    layout = f.cleaned_data.get('layout')
    stylesheet = renderer.get_stylesheet_by_name(
        f.cleaned_data.get('stylesheet'))

    # Determine geographic area
    if osmid is not None:
        try:
            bbox_wkt, area_wkt = renderer.get_geographic_info(osmid)
        except ValueError:
            LOG.exception("Error determining compatible paper sizes")
            raise
        bbox = ocitysmap.coords.BoundingBox.parse_wkt(bbox_wkt)
    else:
        lat_upper_left = f.cleaned_data.get("lat_upper_left")
        lon_upper_left = f.cleaned_data.get("lon_upper_left")
        lat_bottom_right = f.cleaned_data.get("lat_bottom_right")
        lon_bottom_right = f.cleaned_data.get("lon_bottom_right")

        # Check we have correct floats
        if (lat_upper_left == None or lon_upper_left == None
            or lat_bottom_right == None or lon_bottom_right == None):
           return HttpResponseBadRequest("ERROR: Invalid arguments")

        bbox = ocitysmap.coords.BoundingBox(
            lat_upper_left, lon_upper_left,
            lat_bottom_right, lon_bottom_right)

    renderer_cls = ocitysmap.renderers.get_renderer_class_by_name(layout)
    paper_sizes = sorted(renderer_cls.get_compatible_paper_sizes(bbox),
                         key = lambda p: p[1])

    return HttpResponse(content=json_encode(paper_sizes),
                        mimetype='text/json')


def api_bbox(request, osm_id):
    """API handler that returns the bounding box from an OSM ID polygon."""

    try:
        osm_id = int(osm_id)
    except ValueError:
        return HttpResponseBadRequest("ERROR: Invalid arguments")

    renderer = ocitysmap.OCitySMap(www.settings.OCITYSMAP_CFG_PATH)
    try:
        bbox_wkt, area_wkt = renderer.get_geographic_info(osm_id)
        bbox = ocitysmap.coords.BoundingBox.parse_wkt(bbox_wkt)
        return HttpResponse(content=json_encode(bbox.as_json_bounds()),
                            mimetype='text/json')
    except:
        LOG.exception("Error calculating bounding box for OSM ID %d!" % osm_id)

    return HttpResponseBadRequest("ERROR: OSM ID %d not found!" % osm_id)
