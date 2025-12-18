from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts import views as account_views
from core import views as core_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path

urlpatterns = [
    # ... другие URL
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt'
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home, name='home'),
    

    path('login/', account_views.login_view, name='login'),
    path('logout/', account_views.logout_view, name='logout'),
    path('register/', account_views.register_view, name='register'),
    path('profile/', account_views.profile_view, name='profile'),
    

    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset.html',
             email_template_name='auth/password_reset_email.html',
             subject_template_name='auth/password_reset_subject.txt',
             success_url='/password-reset/done/'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html',
             success_url='/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    path('notifications/', include('notifications.urls')),

    path('admin-dashboard/', core_views.admin_dashboard, name='admin_dashboard'),
    path('manage-groups/', core_views.manage_groups, name='manage_groups'),
    path('manage-groups/<int:group_id>/edit/', core_views.edit_group, name='edit_group'),
    path('manage-groups/<int:group_id>/delete/', core_views.delete_group, name='delete_group'),
    path('user-management/', core_views.user_management, name='user_management'),
    path('user-management/add/', core_views.add_user, name='add_user'),
    path('user-management/<int:user_id>/edit/', core_views.edit_user, name='edit_user'),
    path('user-management/<int:user_id>/delete/', core_views.delete_user, name='delete_user'),
    path('api/user/<int:user_id>/', core_views.get_user_api, name='get_user_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    from django.conf.urls.i18n import set_language

urlpatterns += [
    path('i18n/setlang/', set_language, name='set_language'),
]
