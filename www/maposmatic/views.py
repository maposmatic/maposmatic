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

from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from www.maposmatic import helpers, forms, nominatim, models
import www.settings

try:
    from json import dumps as json_encode
except ImportError:
    try:
        from cjson import encode as json_encode
    except ImportError:
        from json import write as json_encode

def rc_add_status(context):
    return {'MAPOSMATIC_DAEMON_RUNNING': www.settings.is_daemon_running()}

class MapOSMaticRequestContext(RequestContext):
    def __init__(self, request):
        RequestContext.__init__(self, request, {}, [rc_add_status])

def index(request):
    """The main page."""
    return render_to_response('maposmatic/index.html',
                              context_instance=MapOSMaticRequestContext(request))

def about(request):
    """The about page."""
    return render_to_response('maposmatic/about.html',
                              context_instance=MapOSMaticRequestContext(request))

def new(request):
    """The map creation page and form."""

    if request.method == 'POST':
        form = forms.MapRenderingJobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.administrative_osmid = form.cleaned_data.get('administrative_osmid')

            existing = helpers.rendering_already_exists(job)
            if existing:
                request.session['redirected'] = True
                return HttpResponseRedirect(reverse('job-by-id',
                                                    args=[existing]))

            job.status = 0 # Submitted
            job.submitterip = request.META['REMOTE_ADDR']
            job.map_language = form.cleaned_data.get('map_language')
            job.index_queue_at_submission = (models.MapRenderingJob.objects
                                             .queue_size())
            job.save()

            return HttpResponseRedirect(reverse('job-by-id',
                                                args=[job.id]))
    else:
        form = forms.MapRenderingJobForm()

    return render_to_response('maposmatic/new.html',
                              { 'form' : form },
                              context_instance=MapOSMaticRequestContext(request))

def job(request, job_id):
    """The job details page.

    Args:
        job_id (int): the job ID in the database.
    """

    job = get_object_or_404(models.MapRenderingJob, id=job_id)
    isredirected = request.session.get('redirected', False)
    request.session.pop('redirected', None)

    refresh = www.settings.REFRESH_JOB_WAITING
    if job.is_rendering():
        refresh = www.settings.REFRESH_JOB_RENDERING

    return render_to_response('maposmatic/job-page.html',
                              { 'job': job, 'single': True,
                                'redirected': isredirected,
                                'refresh': refresh, 'refresh_ms': (refresh*1000) },
                              context_instance=MapOSMaticRequestContext(request))

def all_jobs(request):
    """Displays all jobs from the last 24 hours."""

    one_day_before = datetime.datetime.now() - datetime.timedelta(1)
    job_list = (models.MapRenderingJob.objects.all()
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
                              { 'jobs': jobs,
                                'pages': helpers.get_pages_list(jobs, paginator) },
                              context_instance=MapOSMaticRequestContext(request))

def all_maps(request):
    """Displays all maps, sorted alphabetically, eventually matching the search
    terms, when provided."""

    map_list = None
    form = forms.MapSearchForm(request.GET)

    if form.is_valid():
        map_list = (models.MapRenderingJob.objects
                    .order_by('maptitle')
                    .filter(status=2)
                    .filter(maptitle__icontains=form.cleaned_data['query']))
        if len(map_list) == 1:
            return HttpResponseRedirect(reverse('job-by-id',
                                                args=[map_list[0].id]))
    else:
        form = forms.MapSearchForm()

    if map_list is None:
        map_list = (models.MapRenderingJob.objects.filter(status=2)
                    .filter(resultmsg="ok")
                    .order_by('maptitle'))
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
                              { 'maps': maps, 'letters': helpers.get_letters(),
                                'form': form, 'is_search': form.is_valid(),
                                'pages': helpers.get_pages_list(maps, paginator) },
                              context_instance=MapOSMaticRequestContext(request))

def all_maps_by_letter(request, letter):
    """Displays all maps for the given first-letter."""

    letter = letter[:1].upper()
    map_list = (models.MapRenderingJob.objects.filter(status=2)
                .filter(resultmsg="ok")
                .filter(maptitle__startswith=letter)
                .order_by('maptitle'))
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
                              { 'maps': maps, 'letters': helpers.get_letters(),
                                'current_letter': letter,
                                'form': forms.MapSearchForm() },
                              context_instance=MapOSMaticRequestContext(request))

def query_nominatim(request, format, squery):
    """Nominatim query gateway."""

    format = format or request.GET.get('format', 'json')
    if format not in ['json']:
        return HttpResponseBadRequest("ERROR: Invalid format")

    squery = squery or request.GET.get('q', '')

    try:
        contents = nominatim.query(squery, with_polygons=False)
    except:
        contents = []

    if format == 'json':
        return HttpResponse(content=json_encode(contents),
                            mimetype='text/json')
    # Support other formats here.

def recreate(request):
    if request.method == 'POST':
        form = forms.MapRecreateForm(request.POST)
        if form.is_valid():
            job = get_object_or_404(models.MapRenderingJob,
                                    id=form.cleaned_data['jobid'])

            existing = helpers.rendering_already_exists(job)
            if existing:
                request.session['redirected'] = True
                return HttpResponseRedirect(reverse('job-by-id',
                                                    args=[existing]))

            newjob = models.MapRenderingJob()
            newjob.maptitle = job.maptitle

            newjob.administrative_city = job.administrative_city
            newjob.administrative_osmid = job.administrative_osmid

            newjob.lat_upper_left = job.lat_upper_left
            newjob.lon_upper_left = job.lon_upper_left
            newjob.lat_bottom_right = job.lat_bottom_right
            newjob.lon_bottom_right = job.lon_bottom_right

            newjob.status = 0 # Submitted
            newjob.submitterip = request.META['REMOTE_ADDR']
            newjob.map_language = job.map_language
            newjob.index_queue_at_submission = (models.MapRenderingJob.objects
                                               .queue_size())
            newjob.save()

            return HttpResponseRedirect(reverse('job-by-id',
                                                args=[newjob.id]))

    return HttpResponseBadRequest("ERROR: Invalid request")

