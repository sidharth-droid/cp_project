from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
urlpatterns = [
    path('admin/download/<str:data_type>/', views.download_excel, name='download_excel'),
    path('admin/get_pie_chart_data/<str:time_range>/', views.get_pie_chart_data, name='get_pie_chart_data'),
    path('api/complains/',views.ComplainsList.as_view(),name='complains-list'),
    path('api/complains/<int:pk>/',views.ComplaintDetail.as_view(),name='complain-detail'),
    path('api/link/<str:url>',views.LinkDetail.as_view(),name='link-detail'),
    path('api/phone/<str:number>',views.PhoneDetail.as_view(),name='phone-detail'),
    path('api/email/<str:email>',views.EmailDetail.as_view(),name='email-detail'),
    path('api/fir/',views.FIRList.as_view(),name='fir-list'),
    path('api/fir/<int:pk>',views.FIRDetail.as_view(),name='fir-detail'),
    path('api/login',views.LoginView.as_view(),name='login'),

    path('admin/login/',views.AdminLogin,name='admin_login'),
    path('admin/dashboard/',views.AdminDashboard,name='admin_dashboard'),
    # path('admin/complains/', views.view_complains, name='view_complains'),
    # path('admin/complains/add/', views.add_complain, name='add_complain'),
    # path('admin/complains/edit/<int:complain_id>/', views.edit_complain, name='edit_complain'),
    # path('admin/complains/delete/<int:complain_id>/', views.delete_complain, name='delete_complain'),
    path('admin/report/<int:days>/', views.download_report, name='download_report'),
    path('admin/complains/', views.complain_list_view, name='view_complains'),
    path('admin/complains/add/', views.complain_create_view, name='add_complain'),
    path('admin/complains/<int:pk>/edit/', views.complain_update_view, name='edit_complain'),
    path('admin/complains/<int:pk>/delete/', views.complain_delete_view, name='delete_complain'),
    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/add/', views.user_add, name='user_add'),
    path('admin/users/<int:object_id>/change/', views.user_change, name='user_change'),
    path('admin/users/<int:object_id>/delete/', views.user_delete, name='user_delete'),
    path('admin/groups/', views.group_list, name='custom_group_list'),
    path('admin/groups/add/', views.group_add, name='custom_group_add'),
    path('admin/groups/<int:object_id>/change/', views.group_change, name='group_change'),
    path('admin/groups/<int:object_id>/delete/', views.group_delete, name='group_delete'),
    path('admin/activity/',views.login_activity,name='login_activity'),
    path('admin/logout/',views.logout_handle,name='logout'),
    
    
    # path('truecaller-bot/', views.truecaller_bot_view, name='truecaller-bot'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)