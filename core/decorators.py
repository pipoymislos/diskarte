from django.shortcuts import redirect
from django.contrib import messages

def single_admin_required(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Check if user is the single admin
            if request.user.username == 'admin' or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('login')
        else:
            return redirect('login')
    return wrapper_func