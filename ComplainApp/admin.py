from django.contrib import admin
from .models import Complains
from django.urls import path
from django.shortcuts import render
from django.conf import settings
from .models import AdminActivity
@admin.register(Complains)
class ComplainsAdmin(admin.ModelAdmin):
    list_display = ['ack_number', 'name','mobile_number','address','fraud_type' ,'steps_taken','status','investigating_officer']
    search_fields = ['ack_number', 'name', 'mobile_number','email','steps_taken']
    list_filter = ['status', 'fraud_type','investigating_officer']
    fieldsets = (
        (None, {
            'fields': ('ack_number', 'name', 'mobile_number','address','email')
        }),
        ('Complaint Details', {
            'fields': ('fraud_type', 'steps_taken', 'status','investigating_officer')
        }),
        ('Files', {
            'fields': ('images_videos',)
        }),
    )

class CustomAdmin(admin.AdminSite):
    site_header = "Admin Dashboard"
    site_title =  "Admin Portal"
    index_title = "Welcome To Admin Page"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('truecaller-bot/',self.admin_view(self.truecaller_bot_view),name='truecaller-bot'),
        ]
        return custom_urls + urls
    def truecaller_bot_view(self,request):
         context = {
            'bot_token': settings.TELEGRAM_BOT_TOKEN,
            'chat_id': settings.TELEGRAM_CHAT_ID,  # Example; customize as needed
        }
         return render(request, 'admin/truecaller_bot.html', context)
custom_admin_site = CustomAdmin(name='custom_admin')
custom_admin_site.register(Complains)


@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'ip_address')
    list_filter = ('user',)
    search_fields = ('user__username', 'ip_address')