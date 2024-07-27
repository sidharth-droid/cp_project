from django.contrib import admin
from django.shortcuts import render
from .models import AdminActivity,FIR,Complains
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin


@admin.register(Complains)
class ComplainsAdmin(admin.ModelAdmin):
    list_display = ['Date','ack_number', 'name','mobile_number','address','fraud_type' ,'steps_taken','status','enquiry_officer']
    search_fields = ['ack_number', 'name', 'mobile_number','email','steps_taken']
    list_filter = ['status', 'fraud_type','enquiry_officer']
    fieldsets = (
        (None, {
            'fields': ( 'name', 'mobile_number','address','email')
        }),
        ('Complaint Details', {
            'fields': ('fraud_type', 'steps_taken', 'status','enquiry_officer')
        }),
       
    )
@admin.register(FIR)
class FIRAdmin(admin.ModelAdmin):
    # list_display=[field.name for field in FIR._meta.get_fields()]
    search_fields = ['ack_number','fir_number','name_of_complainant']
    fieldsets=(
        ('Complain Details', {
            'fields': ('complain',)
        }),
        ('FIR Information', {
            'fields': ( 'fir_number', 'place_of_occurrence', 'distance', 'direction', 'date_of_dispatch_from_ps')
        }),
        ('Complainant Details', {
            'fields': ('name_of_complainant', 'residence_of_complainant')
        }),
        ('Accused Details', {
            'fields': ('name_of_accused', 'residence_of_accused')
        }),
        ('Case Details', {
            'fields': ('description', 'section', 'steps_taken_by_io', 'result_of_the_case')
        }),
    )
    
@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'ip_address')
    list_filter = ('user',)
    search_fields = ('user__username', 'ip_address')

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)