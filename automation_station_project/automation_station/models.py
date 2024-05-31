from django.db import models

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, User
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from zoomus import ZoomClient
from automation_station_project.helpers import init_zoom_client
import uuid

class ZoomAuthServerToServer(models.Model):
    name = models.CharField(max_length=255)
    account_id = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='ZoomAuthServerToServer'
    )
    team = models.ManyToManyField(Group, related_name='ZoomAuthServerToServer')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Add your validation logic here
        fields_to_check = [self.account_id, self.client_id, self.client_secret]


        # Validate Zoom credentials
        try:
            client = init_zoom_client(self.client_id, self.client_secret, self.account_id)
            client_request = client.user.me()
            if client_request.status_code not in [200,201,204]:
                raise ValidationError("Invalid Zoom credentials")
        except Exception as e:
            raise ValidationError(f"Failed to communicate with Zoom: {e}")

        # Call the "real" save() method.
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
class CustomUserManager(BaseUserManager):
    
    

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    active_auth = models.ForeignKey(ZoomAuthServerToServer, on_delete=models.SET_NULL, null=True, related_name='+')
    email = models.EmailField(unique=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()   

    USERNAME_FIELD = 'email'

class ZoomServerAuth(models.Model):
    name = models.CharField(max_length=255)
    account_id = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class ZoomPhoneQueue(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_phone_sites'
    )
    cost_center = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100)
    site_id = models.CharField(max_length=100)
    extension_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return "create_call_queue"
    
    def format_failed_collection(self):
         return f"[{self.cost_center}] with extension [{self.extension_number}] failed: task cancelled"
        
class ZoomPhoneQueueMembers(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_phone_queue_members'
    )
    name = models.CharField(max_length=100)
    call_queue_id = models.CharField(max_length=100)
    user_email = models.CharField(max_length=100, blank=True)
    common_area_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return "add_call_queue_members"
    
    def format_failed_collection(self):
        if self.user_email:
            return f"[{self.name}] failed to add [{self.user_email}] failed: task cancelled"
        elif self.common_area_name:
            return f"[{self.name}] failed to add [{self.common_area_name}] failed: task cancelled"

        return f"[{self.name}] failed to add member: task cancelled"

class ZoomPhoneAddSites(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_phone_add_sites'
    )
    name = models.CharField(max_length=100)
    auto_receptionist_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Default Country')
    address_line1 = models.CharField(max_length=100, default='Default Address')
    city = models.CharField(max_length=100, default='Default City')
    zip = models.CharField(max_length=100, default='00000')
    state_code = models.CharField(max_length=100, default='Default State')
    address_line2 = models.CharField(max_length=100, blank=True, null=True, default='Default Address Line 2')
    short_extension_length = models.CharField(max_length=100)
    site_code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return "add_sites"
    
    def format_failed_collection(self):
        return f"[{self.name}] failed to add site: task cancelled"

class ZoomPhoneAddAutoReceptionist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_phone_add_ar'
    )
    name = models.CharField(max_length=100)
    site_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "add_auto_receptionist"
    
    def format_failed_collection(self):
        return f"[{self.name}] failed to add auto receptionist: task cancelled"
        

class ZoomPhoneUpdateAutoReceptionist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_phone_update_ar'
    )
    name = models.CharField(max_length=100)
    cost_center = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    extension_number = models.IntegerField()
    name_change = models.CharField(max_length=100)
    audio_prompt_language = models.CharField(max_length=100)
    timezone = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "update_auto_receptionist"
    
    def format_failed_collection(self):
        return f"[{self.name}] failed to update auto receptionist: task cancelled"


class ZoomPhoneAddCommonAreas(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_phone_add_common_areas'
    )
    calling_plan_code = models.IntegerField()
    country_iso_code = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    extension_number = models.IntegerField()
    site_name = models.CharField(max_length=100)
    timezone = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "add_common_areas"
    
    def format_failed_collection(self):
        return f"[{self.display_name}] failed to add common area: task cancelled"

class ZoomCCQueue(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_cc_create_call_queue'
    )

    queue_name = models.CharField(max_length=100)
    queue_description = models.CharField(max_length=200)
    queue_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "cc_create_call_queue"
    
    def format_failed_collection(self):
        return f"[{self.queue_name}] failed to create cc call queue: task cancelled"

class ZoomCCUpdateQueue(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_cc_update_call_queue'
    )

    queue_name = models.CharField(max_length=100)
    queue_description = models.CharField(max_length=200)
    max_wait_time = models.CharField(max_length=100)
    wrap_up_time = models.CharField(max_length=100)
    max_engagement_in_queue = models.CharField(max_length=100)
    short_abandon_enable = models.CharField(max_length=100)
    short_abandon_threshold = models.CharField(max_length=100)
    channel_types = models.CharField(max_length=100)
    distribution_type = models.CharField(max_length=100)
    distribution_duration_in_seconds = models.CharField(max_length=100)
    connecting_media_id = models.CharField(max_length=100)
    transferring_media_id = models.CharField(max_length=100)
    holding_media_id = models.CharField(max_length=100)
    waiting_room_id = models.CharField(max_length=100)
    message_accept = models.CharField(max_length=100)
    wrap_up_expiration = models.CharField(max_length=100)
    overflow_to_goodbye_message = models.CharField(max_length=200)
    overflow_to_queue_id = models.CharField(max_length=100)
    overflow_to_flow_id = models.CharField(max_length=100)
    overflow_to_inbox_id = models.CharField(max_length=100)
    auto_close_message = models.CharField(max_length=200)
    auto_close_message_enabled = models.CharField(max_length=100)
    auto_close_timeout = models.CharField(max_length=100)
    auto_close_alert_message = models.CharField(max_length=200)
    auto_close_alert_message_enabled = models.CharField(max_length=100)
    auto_close_alert_message_time = models.CharField(max_length=100)
    recording_storage_location = models.CharField(max_length=100)
    service_level_threshold_in_seconds = models.CharField(max_length=100)
    service_level_exclude_short_abandoned_calls = models.CharField(max_length=100)
    service_level_exclude_long_abandoned_calls = models.CharField(max_length=100)
    service_level_exclude_abandoned_quit_engagements = models.CharField(max_length=100)
    service_level_target_in_percentage = models.CharField(max_length=100)
    agent_routing_profile_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "cc_update_call_queue"
    
    def format_failed_collection(self):
        return f"[{self.queue_name}] failed to update cc call queue: task cancelled"

class ZoomCCDisposition(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_cc_create_disposition'
    )
    status = models.CharField(max_length=100)
    disposition_name = models.CharField(max_length=100)
    disposition_description = models.CharField(max_length=200)
    disposition_type = models.CharField(max_length=100)
    sub_disposition_name = models.CharField(max_length=100)
    current_index = models.CharField(max_length=100)
    parent_index = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "cc_create_disposition"
    
    def format_failed_collection(self):
        return f"[{self.disposition_name}] failed to create disposition: task cancelled"


class ZoomCCAddUsers(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_cc_add_users'
    )
    new_user_id = models.CharField(max_length=100)
    user_email = models.CharField(max_length=100)
    role_name = models.CharField(max_length=100)
    country_iso_code = models.CharField(max_length=100)
    client_integration = models.CharField(max_length=100)
    user_access = models.CharField(max_length=100)
    region_id = models.CharField(max_length=100)
    channel_settings = models.CharField(max_length=100)
    multi_channel_engagements = models.CharField(max_length=100, default='false')
    enable = models.CharField(max_length=100, default='false')
    max_agent_load = models.CharField(max_length=100, default='0')
    concurrent_message_capacity = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "cc_add_users"
    
    def format_failed_collection(self):
        if self.user_email:
            return f"[{self.user_email}] failed to add user: task cancelled"
        elif self.user_id: 
            return f"[{self.user_id}] failed to add user: task cancelled"
        else: 
            return f"Failed to add user: task cancelled"

class ZoomCCInbox(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_cc_create_inbox'
    )
    inbox_name = models.CharField(max_length=100)
    inbox_description = models.CharField(max_length=200)
    inbox_type = models.CharField(max_length=100)
    inbox_content_storage_location_code = models.CharField(max_length=100)
    voicemail = models.CharField(max_length=100)
    soft_delete = models.CharField(max_length=100)
    soft_delete_days_limit = models.CharField(max_length=100)
    voicemail_time_limit = models.CharField(max_length=100)
    delete_voicemail_days_limit = models.CharField(max_length=100)
    voicemail_transcription = models.CharField(max_length=100)
    voicemail_notification_by_email = models.CharField(max_length=100)
    enable = models.CharField(max_length=100)
    include_voicemail_file = models.CharField(max_length=100)
    include_voicemail_transcription = models.CharField(max_length=100)
    forward_voicemail_to_emails = models.CharField(max_length=100)
    emails = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return "cc_create_inbox"
    
    def format_failed_collection(self):
        return f"[{self.inbox_name}] failed to create inbox: task cancelled"
    
    
class ZoomEmergencyAlertNotificationV1(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zoom_emergency_alert_notification_v1'
    )
    name = models.CharField(max_length=255)
    emails = models.TextField()
    target_name = models.CharField(max_length=255)

    def __str__(self):
        return "zoom_emergency_alert_notification_v1"
    
class ZoomCreateCommonAreaV1(models.Model):
    PLAN_TYPE_200 = 200
    PLAN_TYPE_CHOICES = [
        (PLAN_TYPE_200, 'US/CA Unlimited')
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zp_create_common_area_v1'
    )
    displayName = models.CharField(max_length=15)
    extensionNumber = models.CharField(max_length=10)
    siteName = models.CharField(max_length=255)
    License = models.IntegerField(choices=PLAN_TYPE_CHOICES)
    phoneCountry = models.CharField(max_length=2, default='US')
    timeZone = models.CharField(max_length=50, default='America/Los_Angeles')
    templateId = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return "zp_create_common_area_v1"
    
class ZPCreateCallQueueV1(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zp_create_call_queue_v1'
    )
    user_extension_ids = models.JSONField()  # Requires Django 3.1 or later
    common_area_extension_ids = models.JSONField()  # Requires Django 3.1 or later
    call_queue_name = models.CharField(max_length=255)
    extensionNumber = models.CharField(max_length=10)
    templateId = models.CharField(max_length=255, blank=True, null=True)
    site_name = models.CharField(max_length=255)
  # Assuming this is a list of user IDs

    def __str__(self):
        return 'zp_create_call_queue_v1'

class CountryInfo(models.Model):
    iso_code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    phone_number_support = models.IntegerField()
    support_toll_free = models.BooleanField()
    support_toll = models.BooleanField()
    has_area_code = models.BooleanField()
    order_pn_has_state = models.BooleanField()
    order_pn_has_city = models.BooleanField()
    has_state = models.BooleanField()
    has_city = models.BooleanField()
    has_zip = models.BooleanField()
    strict_check_address = models.BooleanField()

class CountryDetail(models.Model):
    iso_code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    phone_number_support = models.IntegerField()
    support_toll_free = models.BooleanField()
    support_toll = models.BooleanField()
    has_area_code = models.BooleanField()
    order_pn_has_state = models.BooleanField()
    order_pn_has_city = models.BooleanField()
    has_state = models.BooleanField()
    has_city = models.BooleanField()
    has_zip = models.BooleanField()
    strict_check_address = models.BooleanField()

class EmergencyAddress(models.Model):
    country = models.CharField(max_length=2)
    address_line1 = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state_code = models.CharField(max_length=10)
    house_number = models.CharField(max_length=10)
    street_name = models.CharField(max_length=255)
    street_suffix = models.CharField(max_length=50, blank=True, null=True)
    pre_directional = models.CharField(max_length=10, blank=True, null=True)
    post_directional = models.CharField(max_length=10, blank=True, null=True)
    plus_four = models.CharField(max_length=10, blank=True, null=True)
    level = models.IntegerField(default=0)
    type = models.IntegerField(default=0)
    zip = models.CharField(max_length=10)
    state_id = models.CharField(max_length=50)
    country_info = models.OneToOneField(CountryInfo, on_delete=models.CASCADE)
    country_detail = models.OneToOneField(CountryDetail, on_delete=models.CASCADE)

class AutoReceptionist(models.Model):
    name = models.CharField(max_length=255)
    extension_number = models.CharField(max_length=10, blank=True, null=True)
    open_hour_action = models.IntegerField(default=0)
    close_hour_action = models.IntegerField(default=0)
    holiday_hour_action = models.IntegerField(default=0)

class ZPCreateSiteV1(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zp_create_site_v1'
    )
    name = models.CharField(max_length=255)
    auto_receptionist = models.OneToOneField(AutoReceptionist, on_delete=models.CASCADE)
    emergency_address = models.OneToOneField(EmergencyAddress, on_delete=models.CASCADE)
    sip_zone_id = models.CharField(max_length=50)
    site_code = models.CharField(max_length=10)
    short_extension_length = models.IntegerField()
    ranges = models.JSONField(default=list, blank=True, null=True)
    state_code = models.CharField(max_length=10)
    city = models.CharField(max_length=100)

    def __str__(self):
        return "zp_create_site_v1"

class ZPCreateAutoReceptionistV1(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='zp_create_auto_receptionist_v1'
    )
    name = models.CharField(max_length=255)
    close_hour_action = models.IntegerField(default=0)
    open_hour_action = models.IntegerField(default=0)
    holiday_hour_action = models.IntegerField(default=0)
    template_id = models.CharField(max_length=255, blank=True, null=True)
    siteName = models.CharField(max_length=255)

    def __str__(self):
        return 'zp_create_auto_receptionist_v1'


class Job(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('progress', 'Progress'),
        ('failure', 'Failure'),
        ('executed', 'Executed'),
        ('failed', 'Failed'),
    )
    job_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    job_name = models.CharField(max_length=255)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Updated to use settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='jobs'
    )
    #zoom_phone_site = models.ForeignKey(ZoomPhoneSite, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='scheduled')
    scheduled_time = models.DateTimeField()
    execution_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Job {self.job_id} by {self.user.username}"
    
class JobCollection(models.Model):
    
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('executed', 'Executed'),
        ('progress', 'Progress'),
        ('failed', 'Failed'),
    )
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='scheduled')
    name = models.CharField(max_length=255)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='Collection')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.name

class JobExecutionLogs(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='logs')
    status = models.CharField(max_length=10, choices=Job.STATUS_CHOICES)
    execution_time = models.DateTimeField(auto_now_add=True)
    response_data = models.JSONField(blank=True, null=True)  # Updated to use django.db.models.JSONField
    
    def __str__(self):
        return f"Log for Job {self.job.job_id} at {self.execution_time}"    
    
    

