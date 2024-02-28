from django.contrib import admin

# Register your models here.

# automation_station/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ZoomAuthServerToServer

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'is_active', 'is_staff', 'is_superuser','active_auth']
    list_editable = ('active_auth',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'active_auth')}),
        # Add any other fieldsets for your CustomUser model
    )
    ordering = ['email']
    
@admin.register(ZoomAuthServerToServer)
class ZoomAuthServerToServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_id', 'client_id', 'user', 'display_teams', 'created_at']
    search_fields = ['name', 'account_id', 'client_id', 'user__username']
    
    def display_teams(self, obj):
        return ", ".join([team.name for team in obj.team.all()])
    display_teams.short_description = 'Teams'
    
admin.site.register(CustomUser, CustomUserAdmin)
