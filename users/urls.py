from django.urls import path
from .views import CustomLoginView, CustomLogoutView, index
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', login_required(index), name='index'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]