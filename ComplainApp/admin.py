from django.contrib import admin
from .models import Complains
# Register your models here.
@admin.register(Complains)
class ComplainsAdmin(admin.ModelAdmin):
    list_display = ['ack_number', 'name','mobile_number','fraud_type' ,'steps_taken','status']
    search_fields = ['ack_number', 'name', 'mobile_number','email','steps_taken']
    list_filter = ['status', 'fraud_type']
    fieldsets = (
        (None, {
            'fields': ('ack_number', 'name', 'mobile_number', 'email')
        }),
        ('Complaint Details', {
            'fields': ('fraud_type', 'steps_taken', 'status')
        }),
        ('Files', {
            'fields': ('images_videos',)
        }),
    )