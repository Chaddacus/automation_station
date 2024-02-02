from django.contrib import admin

# Register your models here.

# automation_station/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'is_active', 'is_staff', 'is_superuser']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser')}),
        # Add any other fieldsets for your CustomUser model
    )
    ordering = ['email']
    

admin.site.register(CustomUser, CustomUserAdmin)
