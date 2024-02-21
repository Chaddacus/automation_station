import requests
import logging
import csv

from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect
from requests_oauthlib import OAuth2Session

from django.contrib.auth.models import User
from automation_station.models import CustomUser
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from django.contrib import messages

from django.contrib.contenttypes.models import ContentType
from .models import ZoomPhoneQueue, Job, JobCollection
from django.utils import timezone
from django.conf import settings

from django.db.models import Count

from decouple import config

from io import StringIO
from .models import Job




# Get an instance of a logger
logger = logging.getLogger(__name__)

CLIENT_ID = config('CLIENT_ID')
CLIENT_SECRET = config('CLIENT_SECRET')
REDIRECT_URI = config('REDIRECT_URI')
TOKEN_URL= config('TOKEN_URL')
CALLBACK_URL = config('CALLBACK_URL')
TOKEN_URL = config('TOKEN_URL')
AUTHORIZATION_URL = config('AUTHORIZATION_URL')

zoom = OAuth2Session(CLIENT_ID, redirect_uri=CALLBACK_URL)

User = CustomUser

#standard index view default
class CustomLoginView(auth_views.LoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['zoomlogin_url'] = zoomlogin(self.request)
        

def zp_call_queue_create(request):
    if request.method == 'POST' and 'csv_file' in request.FILES:
        csv_file = request.FILES['csv_file']
        csv_data = csv_file.read().decode('utf-8')

        # Create a single Job instance
        job = Job.objects.create(
            job_name="zoom phone queue create",
            user=request.user,
            status='scheduled',
            scheduled_time=timezone.now(),
            execution_time=None,  # or set a specific time if needed
        )

        reader = csv.DictReader(csv_data.splitlines())
        for row in reader:
            # Create a ZoomPhoneSite instance for each row
            zoom_phone_queue = ZoomPhoneQueue.objects.create(
                user=request.user,
                cost_center=row['cost_center'],
                department=row['department'],
                site_id=row['site_id'],
                extension_number=row['extension_number'],
            )

            # Now create a JobCollection for each ZoomPhoneSite linking it to the created Job
            content_type = ContentType.objects.get_for_model(ZoomPhoneQueue)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {zoom_phone_queue.department}",  # Customize the name as needed
                job=job,
                content_type=content_type,
                object_id=zoom_phone_queue.pk,
            )

        messages.success(request, "The Phone call queue Create Job and associated collections have been successfully added")
        return render(request, 'index.html')  # Redirect to a success page or another relevant view

@login_required
def index(request):
     return render(request, 'index.html')


@login_required
def jobs(request):
     logger.critical("jobs")
     user_id = request.user.id
     jobs = Job.objects.filter(user=request.user).annotate(rows_count=Count('Collection'))
     return render(request, 'jobs.html', {'jobs': jobs})
     
     

@login_required
def settings(request):
     logger.critical("settings")
     return render(request, 'settings.html')

def zoomlogin(request):
     authorization_url, state = zoom.authorization_url(AUTHORIZATION_URL)
     request.session['oauth_state'] = state

     return redirect(authorization_url)


def validate(request):
    #logger.debug(zoom_token)
    if 'zoom_token' in request.session:
          #logger.debug("token in session")

          zoom_token = request.session['zoom_token']
          logger.critical(zoom_token)

          #logger.debug(zoom_token)
          headers = {'Authorization': f'Bearer {zoom_token}'}
          response = requests.get('https://api.zoom.us/v2/users/me', headers=headers)
          logger.critical(response.status_code)
          logger.critical(response.json())
          if response.status_code == 200:
            logger.critical("found user data {}".format(response.json()) )
            return True,response.json()
          else:
            logger.critical("not found user data")
            return False, None
          
    else:
        logger.critical("no token in session")
        return False, None


def find_or_create_user(zoom_user_data):
     logger.critical(zoom_user_data)
     email = zoom_user_data.get('email')
     user, created = User.objects.get_or_create(email=email)
     return user

def callback(request):
            
    redirect_uri = request.build_absolute_uri().replace('http://' + request.get_host(), REDIRECT_URI)
    
    logger.critical(redirect_uri)
   
    token = zoom.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET,
                             authorization_response=redirect_uri)
    logger.critical(token)

    request.session['zoom_token'] = token['access_token']
    

    valid_token,user_data = validate(request)
    request.session['oauth_state'] = valid_token
    user = find_or_create_user(user_data)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request,user)
    # Save the token somewhere for later use...
    return redirect('/')


def csv_to_dict(csv_data):
    reader = csv.DictReader(StringIO(csv_data))
    data = [row for row in reader]
    return data




    