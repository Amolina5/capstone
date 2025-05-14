# recipes/admin.py
from django.contrib import admin
from .models import Recipe, Category, Chef, RecipeRating

class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'get_chef_name', 'category', 'difficulty', 'is_featured', 'created_at')
    list_filter = ('author', 'category', 'difficulty', 'is_featured')
    search_fields = ('title', 'description', 'ingredients')
    prepopulated_fields = {'slug': ('title',)}
    
    def get_chef_name(self, obj):
        
        try:
            chef = Chef.objects.get(user=obj.author)
            return chef.name
        except:
            return obj.author.username if obj.author else "No Chef"
    
    get_chef_name.short_description = 'Chef'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if db_field.name == "author":
            from django.contrib.auth.models import User
            
            chef_users = User.objects.filter(chef_profile__isnull=False)
            kwargs["queryset"] = chef_users
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Category)
admin.site.register(Chef)
admin.site.register(RecipeRating)