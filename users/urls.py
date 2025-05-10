from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Add user-related URLs here
    path('profile/', views.profile, name='profile'),
]