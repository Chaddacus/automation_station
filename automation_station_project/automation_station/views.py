import requests
import logging
import csv, json

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
from .models import ZoomPhoneQueue, Job, JobCollection, ZoomAuthServerToServer,ZoomPhoneQueueMembers, ZoomPhoneAddSites 
from .models import ZoomPhoneAddAutoReceptionist, ZoomPhoneUpdateAutoReceptionist, ZoomPhoneAddCommonAreas
from automation_station_project.tasks import add

from time import sleep
from django.utils import timezone
from django.conf import settings

from django.db.models import Count

from decouple import config

from io import StringIO
from .models import Job
from .models import JobExecutionLogs
from automation_station_project.helpers import site_id, init_zoom_client






# Get an instance of a logger
logger = logging.getLogger(__name__)

CLIENT_ID = config('CLIENT_ID')
CLIENT_SECRET = config('CLIENT_SECRET')
ACCOUNT_ID = config('ACCOUNT_ID')
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

        reader = csv.DictReader(csv_data.splitlines())

        job_created = False
        job = None

        for row in reader:
            if not job_created:
                # Create a single Job instance
                job = Job.objects.create(
                    job_name="zoom phone queue create",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

            # Create a ZoomPhoneSite instance for each row
            zoom_phone_queue = ZoomPhoneQueue.objects.create(
                user=request.user,
                cost_center=row['cost_center'],
                department=row['department'],
                site_id=row['site_name'],
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

        if job_created:
            messages.success(request, "The Phone call queue Create Job and associated collections have been successfully added")
        else:
            messages.warning(request, "No records found in the CSV file")

        return render(request, 'index.html')  # Redirect to a success page or another relevant view


def zp_call_queue_members_create(request):
    if request.method == 'POST' and 'csv_file' in request.FILES:
        csv_file = request.FILES['csv_file']
        csv_data = csv_file.read().decode('utf-8')

        reader = csv.DictReader(csv_data.splitlines())

        job_created = False
        job = None

        for row in reader:
            if not job_created:
                # Create a single Job instance
                job = Job.objects.create(
                    job_name="zoom phone queue members create",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

            # Create a ZoomPhoneQueueMembers instance for each row
            zoom_phone_queue_member = ZoomPhoneQueueMembers.objects.create(
                user=request.user,
                name= row['name'],
                call_queue_id=row['queue_extension'],
                user_email=row['user_email'],
                common_area_name=row['common_area_name'],
            )

            # Now create a JobCollection for each ZoomPhoneQueueMembers linking it to the created Job
            content_type = ContentType.objects.get_for_model(ZoomPhoneQueueMembers)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {zoom_phone_queue_member.name}",  # Customize the name as needed
                job=job,
                content_type=content_type,
                object_id=zoom_phone_queue_member.pk,
            )

        if job_created:
            messages.success(request, "The Phone call queue Members Create Job and associated collections have been successfully added")
        else:
            messages.warning(request, "No records found in the CSV file")

        return render(request, 'index.html')  # Redirect to a success page or another relevant view


def zp_add_sites(request):
    if request.method == 'POST' and 'csv_file' in request.FILES:
        csv_file = request.FILES['csv_file']
        csv_data = csv_file.read().decode('utf-8')

        reader = csv.DictReader(csv_data.splitlines())
        
        job_created = False
        job = None

        for row in reader:
            if not job_created:
                # Create a single Job instance
                job = Job.objects.create(
                    job_name="add sites",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

                # Create a Site instance for each row
            site = ZoomPhoneAddSites.objects.create(
                user=request.user,
                name=row['name'],
                auto_receptionist_name=row['auto_receptionist_name'],
                country = row['country'],
                address_line1= row['address_line1'],
                city= row['city'],
                zip= row['zip'],
                state_code= row['state_code'],
                address_line2= row['address_line2'],
                short_extension_length=row['short_extension_length'],
                site_code=row['site_code'],
            )

            # Now create a JobCollection for each Site linking it to the created Job
            content_type = ContentType.objects.get_for_model(ZoomPhoneAddSites)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {site.name}",  # Customize the name as needed
                job=job,
                content_type=content_type,
                object_id=site.pk,
            )

        if job_created:
            messages.success(request, "The Add Sites Job and associated collections have been successfully added")
        else:
            messages.warning(request, "No records found in the CSV file")

        return render(request, 'index.html')  # Redirect to a success page or another relevant view

def zp_add_auto_receptionist(request): 
    if request.method == 'POST' and 'csv_file' in request.FILES:
        csv_file = request.FILES['csv_file']
        csv_data = csv_file.read().decode('utf-8')

        reader = csv.DictReader(csv_data.splitlines())
        
        job_created = False
        job = None

        for row in reader:
            if not job_created:
                # Create a single Job instance
                job = Job.objects.create(
                    job_name="add auto receptionist",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

                # Create a Site instance for each row
            site = ZoomPhoneAddAutoReceptionist.objects.create(
                user=request.user,
                name=row['name'],
                site_id=row['site_id'],
            )

            # Now create a JobCollection for each Site linking it to the created Job
            content_type = ContentType.objects.get_for_model(ZoomPhoneAddAutoReceptionist)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {site.name}",  # Customize the name as needed
                job=job,
                content_type=content_type,
                object_id=site.pk,
            )

        if job_created:
            messages.success(request, "The Add Auto Receptionists Job and associated collections have been successfully added")
        else:
            messages.warning(request, "No records found in the CSV file")

        return render(request, 'index.html')  # Redirect to a success page or another relevant view

def zp_update_auto_receptionist(request): 
    if request.method == 'POST' and 'csv_file' in request.FILES:
        csv_file = request.FILES['csv_file']
        csv_data = csv_file.read().decode('utf-8')

        reader = csv.DictReader(csv_data.splitlines())
        
        job_created = False
        job = None

        for row in reader:
            if not job_created:
                # Create a single Job instance
                job = Job.objects.create(
                    job_name="update auto receptionist",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

                # Create a Site instance for each row
            site = ZoomPhoneUpdateAutoReceptionist.objects.create(
                user=request.user,
                name=row['name'],
                cost_center=row.get('cost_center'),
                department=row.get('department', ''),
                extension_number=row['extension_number'],
                name_change=row.get('name_change', ''),
                audio_prompt_language=row.get('audio_prompt_language', ''),
                timezone=row.get('timezone', ''),
            )

            # Now create a JobCollection for each Site linking it to the created Job
            content_type = ContentType.objects.get_for_model(ZoomPhoneUpdateAutoReceptionist)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {site.name}",  # Customize the name as needed
                job=job,
                content_type=content_type,
                object_id=site.pk,
            )

        if job_created:
            messages.success(request, "The Update Auto Receptionists Job and associated collections have been successfully added")
        else:
            messages.warning(request, "No records found in the CSV file")

        return render(request, 'index.html')  # Redirect to a success page or another relevant view

def zp_add_common_areas(request): 
    if request.method == 'POST' and 'csv_file' in request.FILES:
        csv_file = request.FILES['csv_file']
        csv_data = csv_file.read().decode('utf-8')

        reader = csv.DictReader(csv_data.splitlines())
        
        job_created = False
        job = None

        for row in reader:
            if not job_created:
                # Create a single Job instance
                job = Job.objects.create(
                    job_name="add common areas",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

                # Create a Site instance for each row
            site = ZoomPhoneAddCommonAreas.objects.create(
                user=request.user,
                calling_plan_code=row['calling_plan_code'],
                country_iso_code=row['country_iso_code'],
                display_name=row['display_name'],
                extension_number=row['extension_number'],
                site_name=row['site_name'],
                timezone=row['timezone']
            )

            # Now create a JobCollection for each Site linking it to the created Job
            content_type = ContentType.objects.get_for_model(ZoomPhoneAddCommonAreas)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {site.display_name}",  # Customize the name as needed
                job=job,
                content_type=content_type,
                object_id=site.pk,
            )

        if job_created:
            messages.success(request, "The Add Common Areas Job and associated collections have been successfully added")
        else:
            messages.warning(request, "No records found in the CSV file")

        return render(request, 'index.html')  # Redirect to a success page or another relevant view


@login_required
def index(request):
    result = add.delay(4, 4)
    #sleep(10)
    print(result.ready())  # Prints True if the task has finished
    print(result.result)  # Prints the task's result, or the exception if the task failed
     
     
    return render(request, 'index.html')


@login_required
def jobs(request):
    logger.critical("jobs")
    user_id = request.user.id
    jobs = Job.objects.filter(user=request.user).exclude(status__in=['executed', 'deleted']).annotate(rows_count=Count('Collection'))
    completed_jobs = Job.objects.filter(user=request.user,status='executed').annotate(rows_count=Count('Collection'))
    return render(request, 'jobs.html', {'jobs': jobs, 'completed_jobs': completed_jobs} )
     
     

@login_required
def settings(request):
    logger.critical("settings")
    logging.critical(request.user)
    user_groups = request.user.groups.all()
    logger.critical(user_groups)
    servertoserver = ZoomAuthServerToServer.objects.filter(team__in=user_groups)
    logger.critical(servertoserver)
    # Get the first matching team for each ZoomAuthServerToServer instance
    matching_teams = {server: server.team.filter(id__in=user_groups).first() for server in servertoserver}
    logger.critical("here" +str(matching_teams))
    
    # Get the first item in the dictionary
    if matching_teams:
        first_key, first_value = next(iter(matching_teams.items()))
        logger.critical(f"First Server: {first_key}, First Team: {first_value}")
   

    return render(request, 'settings.html', {'servertoserver': servertoserver, 'matching_team': matching_teams})

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




def download_data(request, job_id):
    # Get the job
    job = Job.objects.get(id=job_id)

    # Get the job logs
    job_logs = JobExecutionLogs.objects.filter(job_id=job_id)

    # Create a response
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={job.job_name}.txt'

    # Write the job data to the response
    for log in job_logs:
        response_data = log.response_data  # response_data is already a list
        if response_data is not None:
            for item in response_data:
                if isinstance(item, str):
                    response.write(f"{item}, ")
                else:
                    response.write(f"{json.dumps(item)}\n")

    return response