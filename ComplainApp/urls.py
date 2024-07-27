from django.conf import settings
from django.conf.urls.static import static
from django.urls import path,include
from django.shortcuts import redirect
from . import views
urlpatterns = [
    path('admin/download/<str:data_type>/', views.download_excel, name='download_excel'),
    path('admin/download_fir/', views.download_fir, name='download_fir'),

    path('api/complains/<str:pk>/',views.ComplaintDetail.as_view(),name='complain-detail'),
    path('api/complains/create/new/',views.ComplainsCreate.as_view(),name='complain-create'),
    

    path('admin/login/',views.AdminLogin,name='admin_login'),
    path('', lambda request: redirect('admin_login'), name='login_admin'),
    path('admin/dashboard/',views.AdminDashboard,name='admin_dashboard'),
    path('send_otp/', views.send_otp, name='send_otp'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('resend_otp/', views.resend_otp, name='resend_otp'),
    path('delete_file/', views.delete_file_view, name='delete_file'),

    path('admin/complains/', views.complain_list_view, name='view_complains'),
    path('admin/complains/add/', views.complain_create_view, name='add_complain'),
    path('admin/complains/<str:pk>/edit/', views.complain_update_view, name='edit_complain'),
    path('admin/complains/<str:pk>/delete/', views.complain_delete_view, name='delete_complain'),

    path('admin/fir/', views.fir_list_view, name='view_fir'),
    path('admin/fir/add/', views.fir_create_view, name='add_fir'),
    path('admin/fir/<str:pk>/edit/', views.fir_update_view, name='edit_fir'),
    path('admin/fir/<str:pk>/delete/', views.fir_delete_view, name='delete_fir'),
    path('select2/', include('django_select2.urls')),

    path('admin/users/', views.user_list_view, name='user_list'),
    path('admin/users/create/', views.user_create_view, name='user_create'),
    path('admin/users/update/<int:user_id>/', views.user_update_view, name='user_update'),
    path('admin/users/delete/<int:user_id>/', views.user_delete_view, name='user_delete'),

    path('admin/activity/',views.login_activity,name='login_activity'),
    path('admin/activity/<int:activity_id>/delete/',views.delete_login_activity,name='delete_login_activity'),
    path('admin/logout/',views.logout_handle,name='logout-admin'),
   
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)