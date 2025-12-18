from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.role == 'admin'
