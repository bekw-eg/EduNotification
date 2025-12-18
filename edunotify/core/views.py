# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from datetime import date, timedelta
from .models import Notification, Group, CustomUser

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def home(request):
    context = {}
    
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            notifications = Notification.objects.all().order_by('-created_at')[:5]
        else:
            if request.user.group:
                notifications = Notification.objects.filter(
                    Q(notification_type='general') | 
                    Q(group=request.user.group)
                ).order_by('-created_at')[:5]
            else:
                notifications = Notification.objects.filter(
                    notification_type='general'
                ).order_by('-created_at')[:5]
        
        context['notifications'] = notifications
        
        if request.user.role == 'admin':
            context['total_notifications'] = Notification.objects.count()
            context['total_users'] = CustomUser.objects.count()
            context['total_groups'] = Group.objects.count()
            context['admin_count'] = CustomUser.objects.filter(role='admin').count()
    
    return render(request, 'home.html', context)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    admin_count = CustomUser.objects.filter(role='admin').count()
    general_count = Notification.objects.filter(notification_type='general').count()
    group_count = Notification.objects.filter(notification_type='group').count()
    
    context = {
        'total_notifications': Notification.objects.count(),
        'total_users': CustomUser.objects.count(),
        'total_groups': Group.objects.count(),
        'admin_count': admin_count,
        'general_count': general_count,
        'group_count': group_count,
        'today_notifications': Notification.objects.filter(created_at__date=today).count(),
        'recent_activity': Notification.objects.filter(created_at__gte=week_ago).count(),
        'recent_notifications': Notification.objects.all().order_by('-created_at')[:10],
        'recent_users': CustomUser.objects.order_by('-date_joined')[:10],
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def manage_groups(request):
    if request.method == 'POST':
        if 'group_id' in request.POST: 
            group_id = request.POST.get('group_id')
            group = get_object_or_404(Group, id=group_id)
            group.name = request.POST.get('name')
            group.description = request.POST.get('description')
            group.save()
            messages.success(request, 'Группа сәтті жаңартылды!')
        else:  
            name = request.POST.get('name')
            description = request.POST.get('description')
            
            if name:
                Group.objects.create(name=name, description=description)
                messages.success(request, 'Группа сәтті құрылды!')
        
        return redirect('manage_groups')
    
    # ТҮЗЕТІЛГЕН БӨЛІК - customuser емес, members пайдалану керек
    groups = Group.objects.annotate(
        user_count=Count('members'),  # <-- 'customuser' емес, 'members'
        notification_count=Count('notifications')  # <-- 'notification' емес, 'notifications'
    ).order_by('-created_at')
    
    return render(request, 'admin/manage_groups.html', {'groups': groups})

@login_required
@user_passes_test(is_admin)
def edit_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    if request.method == 'POST':
        group.name = request.POST.get('name')
        group.description = request.POST.get('description')
        group.save()
        messages.success(request, 'Группа сәтті жаңартылды!')
        return redirect('manage_groups')
    
    return render(request, 'admin/edit_group.html', {'group': group})

@login_required
@user_passes_test(is_admin)
def delete_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    # customuser_set деп те атауға болады, бірақ models.py бойынша members қолдану керек
    if group.members.exists():  # <-- customuser_set.exists() емес
        messages.error(request, 'Бұл группада пайдаланушылар бар, жою мүмкін емес!')
    else:
        group.delete()
        messages.success(request, 'Группа сәтті жойылды!')
    
    return redirect('manage_groups')

@login_required
@user_passes_test(is_admin)
def user_management(request):
    users = CustomUser.objects.select_related('group').order_by('-date_joined')
    groups = Group.objects.all()
    
    admin_count = users.filter(role='admin').count()
    user_count = users.filter(role='user').count()
    
    context = {
        'users': users,
        'all_groups': groups,
        'admin_count': admin_count,
        'user_count': user_count,
    }
    
    return render(request, 'admin/manage_users.html', context)

@login_required
@user_passes_test(is_admin)
def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'user')
        group_id = request.POST.get('group')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Бұл логин қолданылып тұр!')
            return redirect('user_management')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Бұл email қолданылып тұр!')
            return redirect('user_management')
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role
        )
        
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                user.group = group
                user.save()
            except Group.DoesNotExist:
                pass
        
        messages.success(request, 'Пайдаланушы сәтті қосылды!')
        return redirect('user_management')
    
    return redirect('user_management')

@login_required
@user_passes_test(is_admin)
def get_user_api(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    data = {
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'group_id': user.group.id if user.group else None,
        }
    }
    return JsonResponse(data)

@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.role = request.POST.get('role', 'user')
        
        group_id = request.POST.get('group')
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                user.group = group
            except Group.DoesNotExist:
                user.group = None
        else:
            user.group = None
        
        password = request.POST.get('password')
        if password:
            user.set_password(password)
        
        user.save()
        messages.success(request, 'Пайдаланушы сәтті жаңартылды!')
        return redirect('user_management')
    
    groups = Group.objects.all()
    return render(request, 'admin/edit_user.html', {
        'edit_user': user,
        'groups': groups
    })

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user == request.user:
        messages.error(request, 'Өзіңізді жоя алмайсыз!')
    else:
        user.delete()
        messages.success(request, 'Пайдаланушы сәтті жойылды!')
    
    return redirect('user_management')