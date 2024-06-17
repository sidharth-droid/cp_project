from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
urlpatterns = [
    path('api/complains/',views.ComplainsList.as_view(),name='complains-list'),
    path('api/complains/<int:pk>/',views.ComplaintDetail.as_view(),name='complain-detail'),
    # path('truecaller-bot/', views.truecaller_bot_view, name='truecaller-bot'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)