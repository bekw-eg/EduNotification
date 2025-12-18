from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import CustomUser, Group

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Сәтті кірдіңіз!')
            return redirect('home')
        else:
            messages.error(request, 'Пайдаланушы аты немесе пароль қате')
    
    return render(request, 'auth/login.html') 

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        group_id = request.POST.get('group')
        
        if password1 != password2:
            messages.error(request, 'Парольдер сәйкес емес')
            return redirect('register')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Бұл пайдаланушы аты бос емес')
            return redirect('register')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Бұл электронды пошта бос емес')
            return redirect('register')
        
        group = None
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                pass
        
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password1,
            group=group
        )
        
        login(request, user)
        messages.success(request, 'Тіркелу сәтті аяқталды!')
        return redirect('home')
    
    groups = Group.objects.all()
    return render(request, 'auth/register.html', {'groups': groups}) 

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Сәтті шықтыңыз!')
    return redirect('home')

@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        
        group_id = request.POST.get('group')
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                user.group = group
            except Group.DoesNotExist:
                pass
        
        user.save()
        messages.success(request, 'Профиль сәтті жаңартылды!')
        return redirect('profile')
    
    groups = Group.objects.all()
    return render(request, 'profile.html', {'groups': groups})