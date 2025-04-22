from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

def index(request):
    return render(request, 'users/index.html')

class CustomLoginView(LoginView):
    template_name = 'users/login.html'

class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        return redirect('login')