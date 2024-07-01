from django.contrib import admin
from django.urls.resolvers import URLPattern
from .models import Complains
from django.shortcuts import render
from django.conf import settings
from .models import AdminActivity,ScamEmail,ScamLink,ScamPhone,FIR
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.urls import path
from django.template.response import TemplateResponse
import pandas as pd
import plotly.express as px

@admin.register(Complains)
class ComplainsAdmin(admin.ModelAdmin):
    list_display = ['Date','ack_number', 'name','mobile_number','address','fraud_type' ,'steps_taken','status','investigating_officer']
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
@admin.register(FIR)
class FIRAdmin(admin.ModelAdmin):
    list_display=[field.name for field in FIR._meta.get_fields()]
    search_fields = ['ack_number','fir_number','name_of_complainant']
    fieldsets=(
        ('Complain Details', {
            'fields': ('complain',)
        }),
        ('FIR Information', {
            'fields': ('date', 'fir_number', 'place_of_occurrence', 'distance', 'direction', 'date_of_dispatch_from_ps')
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

@admin.register(ScamPhone)
class ScamPhoneAdmin(admin.ModelAdmin):
    list_display = ('number','status','details','complaints','created_at')
    list_filter = ('status','complaints')
    search_fields = ('number',)
@admin.register(ScamLink)
class ScamLinkAdmin(admin.ModelAdmin):
    list_display = ('url','status','details','complaints','created_at')
    list_filter = ('status','complaints')
    search_fields = ('url',)
@admin.register(ScamEmail)
class ScamEmailAdmin(admin.ModelAdmin):
    list_display = ('email','status','details','complaints','created_at')
    list_filter = ('status','complaints')
    search_fields = ('email',)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Registering the Group model
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
# class AdminReport(admin.ModelAdmin):
#     # site_header = "Fraud Complaint Management"
#     change_list_template = 'admin/reports.html'
    
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('reports/',self.admin_site.admin_view(self.reports_view),name='reports')

#         ]
#         return custom_urls+urls
#     def reports_view(self,request):
#         complains = Complains.objects.all()
#         data = pd.DataFrame(list(complains.values('fraud_type','status','Date')))
#         daily_complains = data.groupby(data['Date'].dt.date).size().reset_index(name='count')
#         daily_plot = px.bar(daily_complains,x='Date',y='count',title='Daily Complaints Received')
#         fraud_type_plot = px.pie(data,names='fraud_type',title='Fraud Type Distribution')
#         closed_data = data[data['status']=='closed']
#         status_counts = closed_data['status'].value_counts().reset_index(name='count')
#         closed_plot = px.bar(status_counts, x='index', y='count', title='Closed Complaints Distribution')

#         context = dict(
#             self.admin_site.each_context(request),
#             daily_plot=daily_plot.to_html(full_html=False),
#             fraud_type_plot=fraud_type_plot.to_html(full_html=False),
#             closed_plot=closed_plot.to_html(full_html=False)
#         )
#         return TemplateResponse(request, "admin/reports.html", context)
# # admin.site.register(AdminReport)
# admin.site.register(AdminReport)




# class CustomAdmin(admin.AdminSite):
#     site_header = "Admin Dashboard"
#     site_title =  "Admin Portal"
#     index_title = "Welcome To Admin Page"

#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('truecaller-bot/',self.admin_view(self.truecaller_bot_view),name='truecaller-bot'),
#         ]
#         return custom_urls + urls
#     def truecaller_bot_view(self,request):
#          context = {
#             'bot_token': settings.TELEGRAM_BOT_TOKEN,
#             'chat_id': settings.TELEGRAM_CHAT_ID,  # Example; customize as needed
#         }
#          return render(request, 'admin/truecaller_bot.html', context)
# custom_admin_site = CustomAdmin(name='custom_admin')
# custom_admin_site.register(Complains)