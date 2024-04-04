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
    active_auth = models.OneToOneField(ZoomAuthServerToServer, on_delete=models.SET_NULL, null=True, related_name='+')
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
    
    

