from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import LoginForm


def login_view(request):
    """
    View for user login. If the user is already logged in, they are redirected to the home page.
    If the user is not logged in, they are presented with a login form. If the form is submitted, the
    user is authenticated and logged in. 
    
    :param request: POST request that is sent with the form submission
    :type request: HttpRequest
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                context = {
                    'login_success': True
                }
                return render(request, 'login.html', context)
            else:
                form.add_error(None, "Invalid username or password")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


def custom_404(request, exception):
    return render(request, '404.html', status=404)
