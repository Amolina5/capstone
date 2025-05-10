from django.urls import path
from . import views

app_name = 'recipes'

urlpatterns = [
    
    path('', views.recipe_list, name='recipe_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('detail/<slug:slug>/', views.recipe_detail, name='recipe_detail'),
    path('add/', views.recipe_add, name='recipe_add'),
    path('edit/<slug:slug>/', views.recipe_edit, name='recipe_edit'),
    path('delete/<slug:slug>/', views.recipe_delete, name='recipe_delete'),
    path('rate/<slug:slug>/', views.recipe_rate, name='recipe_rate'),
    path('chefs/cameron-quinn/', views.chef_cameron_view, name='chef_cameron'),
    path('chefs/cameron/', views.chef_cameron_view, name='chef_cameron'),

]

