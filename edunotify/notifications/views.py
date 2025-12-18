from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
import os

from core.models import Notification, Group, NotificationArchive
from core.decorators import is_admin
from .forms import NotificationForm, ArchiveForm


@login_required
def notifications_list(request):
    """Хабарландырулар тізімі"""
    status_filter = request.GET.get('status', 'active')
    
    if request.user.role == 'admin':
        if status_filter == 'all':
            notifications = Notification.objects.exclude(status='deleted').order_by('-created_at')
        elif status_filter == 'archived':
            notifications = Notification.objects.filter(status='archived').order_by('-created_at')
        elif status_filter == 'active':
            notifications = Notification.objects.filter(status='active').order_by('-created_at')
        else:
            notifications = Notification.objects.filter(status='active').order_by('-created_at')
    else:
        if status_filter == 'archived':
            notifications = Notification.objects.filter(
                status='archived',
                archived_by=request.user
            ).order_by('-archive_date')
        else:
            if request.user.group:
                notifications = Notification.objects.filter(
                    Q(notification_type='general') | 
                    Q(group=request.user.group),
                    status='active'
                ).order_by('-created_at')
            else:
                notifications = Notification.objects.filter(
                    notification_type='general',
                    status='active'
                ).order_by('-created_at')
    
    important_notifications = notifications.filter(is_important=True, status='active')
    
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    groups = None
    if request.user.role == 'admin':
        groups = Group.objects.all()
    
    context = {
        'notifications': page_obj,
        'important_notifications': important_notifications,
        'groups': groups,
        'status_filter': status_filter,
        'page_obj': page_obj,
    }
    
    return render(request, 'notifications/list.html', context)


@login_required
def notification_detail(request, notification_id):
    """Хабарландырудың толық сипаттамасы"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    if not notification.is_accessible_by(request.user):
        messages.error(request, 'Хабарландыру қолжетімсіз!')
        return redirect('notifications')
    
    can_archive = notification.can_archive(request.user)
    
    return render(request, 'notifications/detail.html', {
        'notification': notification,
        'can_archive': can_archive
    })


@login_required
def create_notification(request):
    """Жаңа хабарландыру жасау"""
    if request.method == 'POST':
        form = NotificationForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Алдымен notification сақталып, ID алынады
            notification = form.save(commit=False)
            notification.created_by = request.user
            notification.save()  # Бұл жерде сақтап, ID алу керек
            
            # Ендер суретті жаңарту
            if 'image' in request.FILES:
                notification.image = request.FILES['image']
                notification.save()  # Суретті сақтау
            
            messages.success(request, 'Хабарландыру сәтті жарияланды!')
            return redirect('notification_detail', notification_id=notification.id)
        else:
            # Форма қателерін көрсету
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = NotificationForm()
    
    groups = Group.objects.all()
    return render(request, 'notifications/create.html', {
        'form': form,
        'groups': groups
    })


@login_required
def edit_notification(request, notification_id):
    """Хабарландыруды өңдеу - тек автор немесе админ"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    if not (request.user.role == 'admin' or notification.created_by == request.user):
        messages.error(request, 'Сізде бұл хабарландыруды өңдеу құқығы жоқ!')
        return redirect('notification_detail', notification_id=notification.id)
    
    if request.method == 'POST':
        form = NotificationForm(request.POST, request.FILES, instance=notification)
        
        if form.is_valid():
            old_image = None
            if notification.image:
                old_image = notification.image.path
            
            notification = form.save()

            if 'image' in request.FILES and old_image and os.path.exists(old_image):
                try:
                    os.remove(old_image)
                except:
                    pass
            
            messages.success(request, 'Хабарландыру сәтті жаңартылды!')
            return redirect('notification_detail', notification_id=notification.id)
        else:
            messages.error(request, 'Қателіктерді түзетіңіз')
    
    groups = Group.objects.all()
    return render(request, 'notifications/edit.html', {
        'notification': notification,
        'groups': groups
    })


@login_required
def delete_notification(request, notification_id):
    """Хабарландыруды жою - тек автор немесе админ"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    if not (request.user.role == 'admin' or notification.created_by == request.user):
        messages.error(request, 'Сізде бұл хабарландыруды жою құқығы жоқ!')
        return redirect('notification_detail', notification_id=notification.id)
    
    if request.method == 'POST':
        if notification.image:
            if os.path.exists(notification.image.path):
                try:
                    os.remove(notification.image.path)
                except:
                    pass
        
        notification.delete()
        
        messages.success(request, 'Хабарландыру сәтті жойылды!')
        return redirect('notifications')
    
    return render(request, 'notifications/confirm_delete.html', {
        'notification': notification
    })


@login_required
def archive_notification(request, notification_id):
    """Хабарландыруды архивке қою - барлық пайдаланушылар"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    if not notification.can_archive(request.user):
        messages.error(request, 'Сізде бұл хабарландыруды архивке қою құқығы жоқ!')
        return redirect('notification_detail', notification_id=notification.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        notification.archive(user=request.user, reason=reason)
        
        if hasattr(notification, 'archive_records'):
            NotificationArchive.objects.create(
                notification=notification,
                archived_by=request.user,
                reason=reason
            )
        
        messages.success(request, 'Хабарландыру архивке сәтті ауыстырылды!')
        return redirect('notification_archive')
    
    return render(request, 'notifications/archive_confirm.html', {
        'notification': notification
    })


@login_required
def restore_notification(request, notification_id):
    """Хабарландыруды архивтен қалпына келтіру"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    if not (request.user.role == 'admin' or notification.archived_by == request.user):
        messages.error(request, 'Сізде бұл хабарландыруды қалпына келтіру құқығы жоқ!')
        return redirect('notification_detail', notification_id=notification.id)
    
    if request.method == 'POST':
        notification.restore()
        
        messages.success(request, 'Хабарландыру сәтті қалпына келтірілді!')
        return redirect('notifications')
    
    return render(request, 'notifications/restore_confirm.html', {
        'notification': notification
    })


@login_required
def delete_notification_image(request, notification_id):
    """Хабарландыру суретін жою - тек автор немесе админ"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    if not (request.user.role == 'admin' or notification.created_by == request.user):
        messages.error(request, 'Сізде бұл суретті жою құқығы жоқ!')
        return redirect('notification_detail', notification_id=notification.id)
    
    if request.method == 'POST':
        if notification.image:
            if os.path.exists(notification.image.path):
                try:
                    os.remove(notification.image.path)
                except:
                    pass
            
            notification.image.delete(save=True)
            
            messages.success(request, 'Сурет сәтті жойылды!')
    
    return redirect('edit_notification', notification_id=notification_id)


@login_required
def notification_archive_list(request):
    """Архивтелген хабарландырулар тізімі - барлық пайдаланушылар үшін"""
    if request.user.role == 'admin':
        archived_notifications = Notification.objects.filter(
            status='archived'
        ).order_by('-archive_date')
    else:
        archived_notifications = Notification.objects.filter(
            status='archived',
            archived_by=request.user
        ).order_by('-archive_date')
    
    paginator = Paginator(archived_notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'notifications/archive_list.html', {
        'notifications': page_obj,
        'page_obj': page_obj,
    }) 