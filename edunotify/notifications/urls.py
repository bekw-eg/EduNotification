from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_list, name='notifications'),
    path('create/', views.create_notification, name='create_notification'),
    path('<int:notification_id>/', views.notification_detail, name='notification_detail'),
    path('<int:notification_id>/edit/', views.edit_notification, name='edit_notification'),
    path('<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('<int:notification_id>/archive/', views.archive_notification, name='archive_notification'),
    path('<int:notification_id>/restore/', views.restore_notification, name='restore_notification'),
    path('<int:notification_id>/delete-image/', views.delete_notification_image, name='delete_notification_image'),
    path('archive/', views.notification_archive_list, name='notification_archive'),
]