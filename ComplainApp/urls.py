from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
urlpatterns = [
    path('admin/download/<str:data_type>/', views.download_excel, name='download_excel'),
    path('admin/download_fir/', views.download_fir, name='download_fir'),
    path('admin/report/<int:days>/', views.download_report, name='download_report'),

    path('api/complains/',views.ComplainsList.as_view(),name='complains-list'),
    path('api/complains/<str:pk>/',views.ComplaintDetail.as_view(),name='complain-detail'),
    path('api/complains/create/new/',views.ComplainsCreate.as_view(),name='complain-create'),

    path('api/fir/',views.FIRList.as_view(),name='fir-list'),
    path('api/fir/<str:pk>',views.FIRDetail.as_view(),name='fir-detail'),
    

    path('admin/login/',views.AdminLogin,name='admin_login'),
    path('admin/dashboard/',views.AdminDashboard,name='admin_dashboard'),

    path('admin/complains/', views.complain_list_view, name='view_complains'),
    path('admin/complains/add/', views.complain_create_view, name='add_complain'),
    path('admin/complains/<str:pk>/edit/', views.complain_update_view, name='edit_complain'),
    path('admin/complains/<str:pk>/delete/', views.complain_delete_view, name='delete_complain'),

    path('admin/fir/', views.fir_list_view, name='view_fir'),
    path('admin/fir/add/', views.fir_create_view, name='add_fir'),
    path('admin/fir/<str:pk>/edit/', views.fir_update_view, name='edit_fir'),
    path('admin/fir/<str:pk>/delete/', views.fir_delete_view, name='delete_fir'),

    path('admin/users/', views.user_list_view, name='user_list'),
    path('admin/users/create/', views.user_create_view, name='user_create'),
    path('admin/users/update/<int:user_id>/', views.user_update_view, name='user_update'),
    path('admin/users/delete/<int:user_id>/', views.user_delete_view, name='user_delete'),

    path('admin/activity/',views.login_activity,name='login_activity'),
    path('admin/activity/<int:activity_id>/delete/',views.delete_login_activity,name='delete_login_activity'),
    path('admin/logout/',views.logout_handle,name='logout-admin'),
    path('admin/session_invalidated/', views.session_invalidated, name='session_invalidated'),

    
   
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# -------Unused Routes-----------

    # path('admin/complains/', views.view_complains, name='view_complains'),
    # path('admin/complains/add/', views.add_complain, name='add_complain'),
    # path('admin/complains/edit/<int:complain_id>/', views.edit_complain, name='edit_complain'),
    # path('admin/complains/delete/<int:complain_id>/', views.delete_complain, name='delete_complain'),
    # path('admin/groups/', views.group_list_view, name='group_list'),
    # path('admin/groups/create/', views.group_create_view, name='group_create'),
    # path('admin/groups/update/<int:group_id>/', views.group_update_view, name='group_update'),
    # path('admin/groups/delete/<int:group_id>/', views.group_delete_view, name='group_delete'),
    # path('api/link/<str:url>',views.LinkDetail.as_view(),name='link-detail'),
    # path('api/phone/<str:number>',views.PhoneDetail.as_view(),name='phone-detail'),
    # path('api/email/<str:email>',views.EmailDetail.as_view(),name='email-detail'),
    # path('api/login',views.LoginView.as_view(),name='login'),
    # path('admin/get_pie_chart_data/<str:time_range>/', views.get_pie_chart_data, name='get_pie_chart_data'),
