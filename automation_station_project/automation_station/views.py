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
from .models import ZoomPhoneQueue, Job, JobCollection, ZoomAuthServerToServer,ZoomPhoneQueueMembers, ZoomPhoneAddSites, ZoomCCDisposition, ZoomCCInbox
from .models import ZoomPhoneAddAutoReceptionist, ZoomPhoneUpdateAutoReceptionist, ZoomPhoneAddCommonAreas, ZoomCCQueue, ZoomCCUpdateQueue, ZoomCCAddUsers
from .models import ZoomEmergencyAlertNotificationV1
from automation_station_project.tasks import add

from time import sleep
from django.utils import timezone
from django.conf import settings

from django.db.models import Count

from decouple import config

from io import StringIO
from .models import Job
from .models import JobExecutionLogs
from automation_station_project.helpers import site_id, init_zoom_client, check_utf8, validate_emergency_csv
from automation_station_project.v1api import validate_zoom_pbx_token






# Get an instance of a logger
logger = logging.getLogger(__name__)

CLIENT_ID = config('CLIENT_ID')
CLIENT_SECRET = config('CLIENT_SECRET')
#ACCOUNT_ID = config('ACCOUNT_ID')
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
    
def zcc_call_queue_create(request): 
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
                    job_name="create cc call queue",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

                # Create a Site instance for each row
            site = ZoomCCQueue.objects.create(
                user=request.user,
                queue_name=row['queue_name'],
                queue_description=row['queue_description'],
                queue_type = row['queue_type']
            )

            # Now create a JobCollection for each Site linking it to the created Job
            content_type = ContentType.objects.get_for_model(ZoomCCQueue)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {site.queue_name}",  # Customize the name as needed
                job=job,
                content_type=content_type,
                object_id=site.pk,
            )

        if job_created:
            messages.success(request, "The CC Create Queue Job and associated collections have been successfully added")
        else:
            messages.warning(request, "No records found in the CSV file")

        return render(request, 'index.html')  # Redirect to a success page or another relevant view
    
def zcc_call_queue_update(request): 
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
                    job_name="update cc call queue",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

                # Create a Site instance for each row
            site = ZoomCCUpdateQueue.objects.create(
                user=request.user,
                queue_name=row['queue_name'],
                queue_description=row.get('queue_description', ''), 
                max_wait_time=row.get('max_wait_time', ''),
                wrap_up_time=row.get('wrap_up_time', ''),
                max_engagement_in_queue=row.get('max_engagement_in_queue', ''),
                short_abandon_enable=row.get('short_abandon_enable', ''),
                short_abandon_threshold=row.get('short_abandon_threshold', ''),
                channel_types=row.get('channel_types', ''),
                distribution_type=row.get('distribution_type', ''),
                distribution_duration_in_seconds=row.get('distribution_duration_in_seconds', ''),
                connecting_media_id=row.get('connecting_media_id', ''),
                transferring_media_id=row.get('transferring_media_id', ''),
                holding_media_id=row.get('holding_media_id', ''),
                waiting_room_id=row.get('waiting_room_id', ''),
                message_accept=row.get('message_accept', ''),
                wrap_up_expiration=row.get('wrap_up_expiration', ''),
                overflow_to_goodbye_message=row.get('overflow_to_goodbye_message', ''),
                overflow_to_queue_id=row.get('overflow_to_queue_id', ''),
                overflow_to_flow_id=row.get('overflow_to_flow_id', ''),
                overflow_to_inbox_id=row.get('overflow_to_inbox_id', ''),
                auto_close_message=row.get('auto_close_message', ''),
                auto_close_message_enabled=row.get('auto_close_message_enabled', ''),
                auto_close_timeout=row.get('auto_close_timeout', ''),
                auto_close_alert_message=row.get('auto_close_alert_message', ''),
                auto_close_alert_message_enabled=row.get('auto_close_alert_message_enabled', ''),
                auto_close_alert_message_time=row.get('auto_close_alert_message_time', ''),
                recording_storage_location=row.get('recording_storage_location', ''),
                service_level_threshold_in_seconds=row.get('service_level_threshold_in_seconds', ''),
                service_level_exclude_short_abandoned_calls=row.get('service_level_exclude_short_abandoned_calls', ''),
                service_level_exclude_long_abandoned_calls=row.get('service_level_exclude_long_abandoned_calls', ''),
                service_level_exclude_abandoned_quit_engagements=row.get('service_level_exclude_abandoned_quit_engagements', ''),
                service_level_target_in_percentage=row.get('service_level_target_in_percentage', ''),
                agent_routing_profile_id=row.get('agent_routing_profile_id', '')
            )

            # Now create a JobCollection for each Site linking it to the created Job
            content_type = ContentType.objects.get_for_model(ZoomCCUpdateQueue)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {site.queue_name}",  # Customize the name as needed
                job=job,
                content_type=content_type,
                object_id=site.pk,
            )

        if job_created:
            messages.success(request, "The CC Update Queue Job and associated collections have been successfully added")
        else:
            messages.warning(request, "No records found in the CSV file")

        return render(request, 'index.html')  # Redirect to a success page or another relevant view

def zcc_create_disposition(request): 
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
                    job_name="create cc disposition",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

                # Create a Site instance for each row
            site = ZoomCCDisposition.objects.create(
                user=request.user,
                status = row.get('status', ''),
                disposition_name = row.get('disposition_name', ''),
                disposition_description = row.get('disposition_description', ''),
                disposition_type = row.get('disposition_type', ''),
                sub_disposition_name = row.get('sub_disposition_name', ''),
                current_index = row.get('current_index', ''),
                parent_index = row.get('parent_index', ''),
            )

            # Now create a JobCollection for each Site linking it to the created Job
            content_type = ContentType.objects.get_for_model(ZoomCCDisposition)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {site.disposition_name}",  # Customize the name as needed
                job=job,
                content_type=content_type,
                object_id=site.pk,
            )

        if job_created:
            messages.success(request, "The CC Create Disposition Job and associated collections have been successfully added")
        else:
            messages.warning(request, "No records found in the CSV file")

        return render(request, 'index.html')  # Redirect to a success page or another relevant view


def zcc_add_users(request): 
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
                    job_name="add cc users",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

                # Create a Site instance for each row
            site = ZoomCCAddUsers.objects.create(
                user=request.user,
                new_user_id = row.get('user_id', ''),
                user_email = row.get('user_email', ''),
                role_name = row.get('role_name', ''),
                country_iso_code = row.get('country_iso_code', ''),
                client_integration = row.get('client_integration', ''),
                user_access = row.get('user_access', ''),
                region_id = row.get('region_id', ''),
                channel_settings = row.get('channel_settings', ''),
                multi_channel_engagements = row.get('multi_channel_engagements', ''),
                enable = row.get('enable', ''),
                max_agent_load = row.get('max_agent_load', ''),
                concurrent_message_capacity = row.get('concurrent_message_capacity', ''),
            )

            # Now create a JobCollection for each Site linking it to the created Job
            content_type = ContentType.objects.get_for_model(ZoomCCAddUsers)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {site.new_user_id}" if site.new_user_id else f"Job for {site.user_email}",
                job=job,
                content_type=content_type,
                object_id=site.pk,
            )

        if job_created:
            messages.success(request, "The CC Add users Job and associated collections have been successfully added")
        else:
            messages.warning(request, "No records found in the CSV file")

        return render(request, 'index.html')  # Redirect to a success page or another relevant view

def zcc_create_inbox(request): 
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
                    job_name="create cc inbox",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

                # Create a Site instance for each row
            site = ZoomCCInbox.objects.create(
                user=request.user,
                inbox_name = row.get('inbox_name', ''),
                inbox_description = row.get('inbox_description', ''),   
                inbox_type = row.get('inbox_type', ''),
                inbox_content_storage_location_code = row.get('inbox_content_storage_location_code', ''),
                voicemail = row.get('voicemail', ''),
                soft_delete =  row.get('soft_delete', ''),
                soft_delete_days_limit = row.get('soft_delete_days_limit', ''),
                voicemail_time_limit =  row.get('voicemail_time_limit', ''),
                delete_voicemail_days_limit =  row.get('delete_voicemail_days_limit', ''),
                voicemail_transcription = row.get('voicemail_transcription', ''), 
                voicemail_notification_by_email = row.get('voicemail_notification_by_email', ''), 
                enable = row.get('enable', ''),
                include_voicemail_file = row.get('include_voicemail_file', ''), 
                include_voicemail_transcription = row.get('include_voicemail_transcription', ''),
                forward_voicemail_to_emails = row.get('forward_voicemail_to_emails', ''), 
                emails =  row.get('emails', ''),
                created_at =  row.get('created_at', ''),
                        )

            # Now create a JobCollection for each Site linking it to the created Job
            content_type = ContentType.objects.get_for_model(ZoomCCInbox)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {site.inbox_name}",  # Customize the name as needed
                job=job,
                content_type=content_type,
                object_id=site.pk,
            )

        if job_created:
            messages.success(request, "The CC Create Inbox Job and associated collections have been successfully added")
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
    print("settings")
    logger.critical("settings")
    logging.critical(request.user)
    user_groups = request.user.groups.all()
    logger.critical(user_groups)
    
    servertoserver = ZoomAuthServerToServer.objects.filter(team__in=user_groups)
    logger.critical(servertoserver)
    # Get the first matching team for each ZoomAuthServerToServer instance
    matching_teams = {server: server.team.filter(id__in=user_groups).first() for server in servertoserver}
    logger.critical("teams " +str(matching_teams))
    
    # Get the first item in the dictionary
    if matching_teams:
        first_key, first_value = next(iter(matching_teams.items()))
        logger.critical(f"First Server: {first_key}, First Team: {first_value}")

    if request.method == 'POST':
        token = request.POST.get('pbx_token')
        if token:
            request.session['zoom_pbx_token'] = token

            if not validate_token(request):
                
                return redirect('settings')

            messages.success(request, "Token successfully saved")
        else:
            messages.warning(request, "No token found in the request")
        
        return redirect('settings')
    
    print(servertoserver)

    return render(request, 'settings.html', {'servertoserver': servertoserver, 'matching_team': matching_teams})


def emergency_alert_notification_v1(request):

    if request.method == 'POST' and 'csv_file' in request.FILES:
        
        if not validate_token(request):
            return redirect('settings')
            
            
        
        csv_file = request.FILES['csv_file']
        csv_data = csv_file.read().decode('utf-8')

        reader = csv.DictReader(csv_data.splitlines())
        
        job_created = False
        job = None

        for row in reader:
            if not job_created:
                # Create a single Job instance
                job = Job.objects.create(
                    job_name="emergency alert notification v1",
                    user=request.user,
                    status='scheduled',
                    scheduled_time=timezone.now(),
                    execution_time=None,  # or set a specific time if needed
                )
                job_created = True

            alert_notification = ZoomEmergencyAlertNotificationV1.objects.create(
                user=request.user,
                name = row.get('name', ''),
                emails = row.get('emails', ''),
                target_name = row.get('target_name', ''),
            )

            content_type = ContentType.objects.get_for_model(ZoomEmergencyAlertNotificationV1)
            JobCollection.objects.create(
                status='scheduled',  # or any other initial status
                name=f"Job for {alert_notification.name}",  # Customize the name as needed
                job=job,
                content_type=content_type,
                object_id=alert_notification.pk,
            )

        if job_created:
            messages.success(request, "Emergency Alert Notification V1 Job and associated collections have been successfully added")
        else:
            messages.warning(request, "No records found in the CSV file")

        return render(request, 'index.html')  # Redirect to a success page or another relevant view

                # Create a Site instance for each row

def validate_token(request):
    
    if not request.session.get('zoom_pbx_token'):
        print("in pre validate not token in request")
        messages.warning(request, "No valid token found. Please submit your token into the settings page")

        return False
    
    if not validate_zoom_pbx_token(request):
        messages.warning(request, "Your token is not valid, please submit a new token.")
        return False
    return True
       

    

    
    

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