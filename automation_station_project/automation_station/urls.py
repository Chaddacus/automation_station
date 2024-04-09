from django.urls import path
from django.contrib.auth import views as auth_views 
from django.views.generic import TemplateView
from django.urls import re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('zoomlogin', views.zoomlogin, name='zoomlogin'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('callback', views.callback, name='callback'),
    path('zp_call_queue_create', views.zp_call_queue_create, name='zp_call_queue_create'),
    path('zp_call_queue_members_create', views.zp_call_queue_members_create, name='zp_call_queue_members_create'),
    path('zp_add_sites', views.zp_add_sites, name='zp_add_sites'),
    path('zp_add_auto_receptionist', views.zp_add_auto_receptionist, name='zp_add_auto_receptionist'),
    path('zp_update_auto_receptionist', views.zp_update_auto_receptionist, name='zp_update_auto_receptionist'),
    path('zp_add_common_areas', views.zp_add_common_areas, name='zp_add_common_areas'),
    path('zcc_call_queue_create', views.zcc_call_queue_create, name='zcc_call_queue_create'),
    path('zcc_call_queue_update', views.zcc_call_queue_update, name='zcc_call_queue_update'),
    path('jobs', views.jobs, name='jobs'),
    path('settings', views.settings, name='settings'),
    path('download_data/<int:job_id>/', views.download_data, name='download_data'),
    re_path('.*', TemplateView.as_view(template_name='index.html')),
]