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
    path('jobs', views.jobs, name='jobs'),
    path('settings', views.settings, name='settings'),
    re_path('.*', TemplateView.as_view(template_name='index.html')),
]