from django.urls import path
from django.contrib.auth import views as auth_views 

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('zoomlogin', views.zoomlogin, name='zoomlogin'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('callback', views.callback, name='callback')
]