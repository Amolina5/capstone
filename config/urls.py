# Add to config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from recipes.views import (
    chefs_view, chef_cameron_view, chef_alex_view, chef_wade_view, 
    recipes_view, chef_couple_view, chef_amanda_view  # Add chef_amanda_view
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='pages/home.html'), name='home'),
    path('recipes/', include('recipes.urls')),
    path('users/', include('users.urls')),
    path('chefs/', chefs_view, name='chefs'),
    path('chefs/cameron/', chef_cameron_view, name='chef_cameron'),
    path('chefs/alex/', chef_alex_view, name='chef_alex'),
    path('chefs/wade/', chef_wade_view, name='chef_wade'),
    path('chefs/couple/', chef_couple_view, name='chef_couple'),
    path('chefs/amanda/', chef_amanda_view, name='chef_amanda'),  # Add this line
    path('all-recipes/', recipes_view, name='all_recipes'),
    path('all-recipes/', recipes_view, name='all_recipes'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)