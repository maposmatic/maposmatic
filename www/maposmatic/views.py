# Create your views here.

from django.forms.util import ErrorList
from django.forms import ChoiceField, RadioSelect, ModelForm, ValidationError
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from www.maposmatic.models import MapRenderingJob
import datetime

class MapRenderingJobForm(ModelForm):
    class Meta:
        model = MapRenderingJob
        fields = ('maptitle', 'administrative_city', 'lat_upper_left', 'lon_upper_left',
                  'lat_bottom_right', 'lon_bottom_right')

    modes = (('admin', 'Administrative boundary'),
             ('bbox', 'Bounding box'))
    mode = ChoiceField(choices=modes, initial='admin', widget=RadioSelect)

    def clean(self):
        cleaned_data = self.cleaned_data

        mode = cleaned_data.get("mode")
        city = cleaned_data.get("administrative_city")

        if mode == 'admin' and city == "":
            msg = u"Administrative city required"
            self._errors["administrative_city"] = ErrorList([msg])
            del cleaned_data["administrative_city"]

        if mode == 'bbox':
            for f in [ "lat_upper_left", "lon_upper_left",
                       "lat_bottom_right", "lon_bottom_right" ]:
                val = cleaned_data.get(f)
                msg = u"Required"
                self._errors[f] = ErrorList([msg])
                del cleaned_data[f]

        return cleaned_data

def index(request):
    if request.method == 'POST':
        form = MapRenderingJobForm(request.POST)
        if form.is_valid():
            job = MapRenderingJob()
            job.maptitle = form.cleaned_data['maptitle']
            job.administrative_city = form.cleaned_data['administrative_city']
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
                              { 'form' : form })

def job(request, job_id):
    job = get_object_or_404(MapRenderingJob, id=job_id)
    return render_to_response('maposmatic/job.html',
                              { 'job' : job })

def all_jobs(request):
    one_day_before = datetime.datetime.now() - datetime.timedelta(1)
    jobs = MapRenderingJob.objects.all().order_by('-submission_time').filter(submission_time__gte=one_day_before)
    return render_to_response('maposmatic/all_jobs.html',
                              { 'jobs' : jobs })

def all_maps(request):
    return render_to_response('maposmatic/all_maps.html')

def about(request):
    return render_to_response('maposmatic/about.html')
