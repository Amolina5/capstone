from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Avg
from django.http import HttpResponse
from django.template import TemplateDoesNotExist
from .models import Recipe, Category, RecipeRating, Chef
from .forms import RecipeForm, RatingForm

def home_view(request):

    featured_recipes = Recipe.objects.filter(is_featured=True)[:6]
    
    latest_recipes = Recipe.objects.order_by('-created_at')[:6]
    
    categories = Category.objects.all()
    
    featured_chefs = Chef.objects.all()[:3]
    
    context = {
        'featured_recipes': featured_recipes,
        'latest_recipes': latest_recipes,
        'categories': categories,
        'featured_chefs': featured_chefs,
    }
    return render(request, 'pages/home.html', context)

def recipe_list(request):
   
    recipes = Recipe.objects.all()
    
    
    categories = Category.objects.all()
    
  
    category_slug = request.GET.get('category')
    if category_slug:
        recipes = recipes.filter(category__slug=category_slug)
    
  
    difficulty = request.GET.get('difficulty')
    if difficulty:
        recipes = recipes.filter(difficulty=difficulty)
    
   
    chef_slug = request.GET.get('chef')
    if chef_slug:
        chef = get_object_or_404(Chef, slug=chef_slug)
        if chef.user:
            recipes = recipes.filter(author=chef.user)
    
    context = {
        'recipes': recipes,
        'categories': categories,
        'selected_category': category_slug,
        'selected_difficulty': difficulty,
        'selected_chef': chef_slug,
    }
    return render(request, 'recipes/recipe_list.html', context)

def recipe_detail(request, slug):
    
    recipe = get_object_or_404(Recipe, slug=slug)
    
    rating_form = RatingForm()
    
    user_rating = None
    if request.user.is_authenticated:
        user_rating = RecipeRating.objects.filter(recipe=recipe, user=request.user).first()
    
    related_by_category = Recipe.objects.filter(category=recipe.category).exclude(id=recipe.id)[:3]
    related_by_chef = Recipe.objects.filter(author=recipe.author).exclude(id=recipe.id)[:3]
    
    try:
        chef = Chef.objects.get(user=recipe.author)
    except Chef.DoesNotExist:
        chef = None
    
    context = {
        'recipe': recipe,
        'rating_form': rating_form,
        'user_rating': user_rating,
        'related_by_category': related_by_category,
        'related_by_chef': related_by_chef,
        'chef': chef,
    }
    
    try:
        return render(request, 'recipes/recipe_detail.html', context)
    except TemplateDoesNotExist:
        html_content = f"""
        <html>
        <head>
            <title>{recipe.title} | Cookbook</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #333; }}
                .meta {{ color: #666; margin-bottom: 20px; }}
                .section {{ margin-bottom: 30px; }}
                .back-button {{ display: inline-block; padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
                img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{recipe.title}</h1>
                
                <div class="meta">
                    <p>
                        <strong>Category:</strong> {recipe.category.name}<br>
                        <strong>Chef:</strong> {recipe.author.username}<br>
                        <strong>Difficulty:</strong> {recipe.difficulty.title()}<br>
                        <strong>Prep Time:</strong> {recipe.prep_time} mins<br>
                        <strong>Cook Time:</strong> {recipe.cook_time} mins<br>
                        <strong>Servings:</strong> {recipe.servings}
                    </p>
                </div>
                
                {f'<img src="{recipe.image.url}" alt="{recipe.title}">' if recipe.image else ''}
                
                <div class="section">
                    <h2>Description</h2>
                    <p>{recipe.description.replace(chr(10), '<br>')}</p>
                </div>
                
                <div class="section">
                    <h2>Ingredients</h2>
                    <p>{recipe.ingredients.replace(chr(10), '<br>')}</p>
                </div>
                
                <div class="section">
                    <h2>Instructions</h2>
                    <p>{recipe.instructions.replace(chr(10), '<br>')}</p>
                </div>
                
                <a href="javascript:history.back()" class="back-button">Back</a>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_content)

def category_detail(request, slug):
  
    category = get_object_or_404(Category, slug=slug)
    
    
    recipes = Recipe.objects.filter(category=category)
    
    context = {
        'category': category,
        'recipes': recipes,
    }
    return render(request, 'recipes/category_detail.html', context)

@login_required
def recipe_add(request):
   
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.save()
            messages.success(request, 'Recipe added successfully!')
            return redirect('recipes:recipe_detail', slug=recipe.slug)
    else:
        form = RecipeForm()
    
    context = {
        'form': form,
        'title': 'Add Recipe',
    }
    return render(request, 'recipes/recipe_form.html', context)

@login_required
def recipe_edit(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug)
    

    if recipe.author != request.user:
        messages.error(request, "You can't edit recipes that you didn't create.")
        return redirect('recipes:recipe_detail', slug=recipe.slug)
    
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recipe updated successfully!')
            return redirect('recipes:recipe_detail', slug=recipe.slug)
    else:
        form = RecipeForm(instance=recipe)
    
    context = {
        'form': form,
        'title': 'Edit Recipe',
        'recipe': recipe,
    }
    return render(request, 'recipes/recipe_form.html', context)

@login_required
def recipe_delete(request, slug):

    recipe = get_object_or_404(Recipe, slug=slug)
    
    if recipe.author != request.user:
        messages.error(request, "You can't delete recipes that you didn't create.")
        return redirect('recipes:recipe_detail', slug=recipe.slug)
    
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Recipe deleted successfully!')
        return redirect('recipes:recipe_list')
    
    context = {
        'recipe': recipe,
    }
    return render(request, 'recipes/recipe_confirm_delete.html', context)

@login_required
def recipe_rate(request, slug):

    recipe = get_object_or_404(Recipe, slug=slug)
    
    if request.method == 'POST':
        rating, created = RecipeRating.objects.get_or_create(
            recipe=recipe,
            user=request.user,
            defaults={
                'rating': request.POST.get('rating'),
                'comment': request.POST.get('comment', '')
            }
        )
        
        if not created:
            rating.rating = request.POST.get('rating')
            rating.comment = request.POST.get('comment', '')
            rating.save()
        
        messages.success(request, 'Thank you for rating this recipe!')
        
    return redirect('recipes:recipe_detail', slug=slug)

def chefs_view(request):

    chefs = Chef.objects.all()
    
    for chef in chefs:
        if chef.user:
            chef.featured_recipe = Recipe.objects.filter(
                author=chef.user, 
                is_featured=True
            ).first()

            chef.recipe_count = Recipe.objects.filter(
                author=chef.user
            ).count()
            
            chef.avg_rating = Recipe.objects.filter(
                author=chef.user
            ).annotate(
                avg_rating=Avg('ratings__rating')
            ).aggregate(Avg('avg_rating'))['avg_rating__avg'] or 0
        else:
            chef.featured_recipe = None
            chef.recipe_count = 0
            chef.avg_rating = 0
    
    # Get featured recipes for the signature dishes section
    featured_recipes = Recipe.objects.filter(is_featured=True)[:5]
    
    context = {
        'chefs': chefs,
        'featured_recipes': featured_recipes
    }
    
    return render(request, 'pages/chefs.html', context)

def recipes_view(request):

    chefs = Chef.objects.exclude(user__isnull=True)
    
    categories = Category.objects.all()
    
    category_slug = request.GET.get('category', '') 
    category_filter = None
    
    if category_slug and category_slug != '':
        try:
            category_filter = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            pass
    
    chefs_with_recipes = []
    
    for chef in chefs:
        chef_recipes = Recipe.objects.filter(author=chef.user)
        
        if category_filter:
            chef_recipes = chef_recipes.filter(category=category_filter)
        
        chef.recipes = chef_recipes.order_by('-created_at')[:6]
        chef.recipe_count = chef_recipes.count()

        chefs_with_recipes.append(chef)

    if category_filter:
        total_recipes = Recipe.objects.filter(category=category_filter).count()
    else:
        total_recipes = Recipe.objects.count()
    
    context = {
        'chefs': chefs_with_recipes,
        'categories': categories,
        'selected_category': category_slug,
        'recipe_count': total_recipes,
        'chef_count': len(chefs_with_recipes),
        'debug_info': {
            'filter_applied': category_filter is not None,
            'filter_name': category_filter.name if category_filter else 'None',
            'chefs_count': len(chefs_with_recipes),
        }
    }
    
    return render(request, 'pages/recipes.html', context)


def chef_detail_view(request, slug):

    chef = get_object_or_404(Chef, slug=slug)
    
    if chef.user:
        recipes = Recipe.objects.filter(author=chef.user).order_by('-created_at')
        featured_recipes = recipes.filter(is_featured=True)[:3]
        recipe_count = recipes.count()
        
        categories = recipes.values('category__name').distinct()
        latest_recipe = recipes.first()
    else:
        recipes = []
        featured_recipes = []
        recipe_count = 0
        categories = []
        latest_recipe = None
    
    context = {
        'chef': chef,
        'recipes': recipes,
        'featured_recipes': featured_recipes,
        'recipe_count': recipe_count,
        'chef_name': chef.name,
        'categories': categories,
        'latest_recipe': latest_recipe,
    }
    
    try:
        return render(request, 'recipes/chef_detail.html', context)
    except TemplateDoesNotExist:
 
        html_content = f"""
        <html>
        <head>
            <title>{chef.name} - Chef Profile | Cookbook</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                h1 {{ color: #333; }}
                .chef-image {{ max-width: 300px; border-radius: 50%; }}
                .recipe-grid {{ display: flex; flex-wrap: wrap; gap: 20px; margin-top: 30px; }}
                .recipe-card {{ width: 300px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
                .recipe-card img {{ width: 100%; height: 200px; object-fit: cover; }}
                .recipe-card-body {{ padding: 15px; }}
                .back-button {{ display: inline-block; padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div style="display: flex; gap: 30px; margin-bottom: 30px;">
                    {f'<img src="{chef.image.url}" alt="{chef.name}" class="chef-image">' if chef.image else ''}
                    <div>
                        <h1>{chef.name}</h1>
                        <p><strong>Specialty:</strong> {chef.specialty}</p>
                        <p><strong>Recipes:</strong> {recipe_count}</p>
                        <div>
                            {f'<a href="{chef.instagram}">Instagram</a> ' if chef.instagram else ''}
                            {f'<a href="{chef.twitter}">Twitter</a> ' if chef.twitter else ''}
                            {f'<a href="{chef.youtube}">YouTube</a>' if chef.youtube else ''}
                        </div>
                    </div>
                </div>
                
                <div>
                    <h2>Biography</h2>
                    <p>{chef.bio.replace(chr(10), '<br>')}</p>
                </div>
                
                <div>
                    <h2>Recipes by {chef.name}</h2>
                    <div class="recipe-grid">
                        {''.join([f"""
                            <div class="recipe-card">
                                {f'<img src="{recipe.image.url}" alt="{recipe.title}">' if recipe.image else ''}
                                <div class="recipe-card-body">
                                    <h3>{recipe.title}</h3>
                                    <p>{recipe.description[:100]}...</p>
                                    <p><strong>Category:</strong> {recipe.category.name}</p>
                                    <p><strong>Difficulty:</strong> {recipe.difficulty.title()}</p>
                                    <p><strong>Time:</strong> {recipe.prep_time + recipe.cook_time} mins</p>
                                </div>
                            </div>
                        """ for recipe in recipes[:6]])}
                    </div>
                </div>
                
                <a href="javascript:history.back()" class="back-button">Back</a>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_content)

def chef_cameron_view(request):
    try:
        cameron_user = User.objects.get(username='Cameron')
        chef = Chef.objects.get(user=cameron_user)
        
        recipes = Recipe.objects.filter(author=cameron_user).order_by('-created_at')
        
        # TEMPORARY DEBUG - remove after testing
        print(f"Found user: {cameron_user}")
        print(f"Found chef: {chef}")
        print(f"Recipe count: {recipes.count()}")
        print(f"Recipes: {[r.title for r in recipes]}")
        
        featured_recipes = recipes.filter(is_featured=True)[:3]
        recipe_count = recipes.count()
        recent_recipes = recipes[:5]
        
    except (User.DoesNotExist, Chef.DoesNotExist) as e:
        print(f"ERROR: {e}")  # TEMPORARY DEBUG
        chef = None
        recipes = []
        featured_recipes = []
        recent_recipes = []
        recipe_count = 0
    
    context = {
        'chef': chef,
        'recipes': recipes,
        'featured_recipes': featured_recipes,
        'recent_recipes': recent_recipes,
        'recipe_count': recipe_count,
        'chef_name': 'Cameron Quinn'
    }
    
    return render(request, 'cameron.html', context)

def chef_alex_view(request):
    try:
        alex_user = User.objects.get(username='alex-molina')
        chef = Chef.objects.get(user=alex_user)
        
        recipes = Recipe.objects.filter(author=alex_user).order_by('-created_at')
        featured_recipes = recipes.filter(is_featured=True)[:3]
        recipe_count = recipes.count()
        
 
        categorized_recipes = {}
        for recipe in recipes:
            category_name = recipe.category.name
            if category_name not in categorized_recipes:
                categorized_recipes[category_name] = []
            categorized_recipes[category_name].append(recipe)
        
    except (User.DoesNotExist, Chef.DoesNotExist):

        chef = None
        recipes = []
        featured_recipes = []
        recipe_count = 0
        categorized_recipes = {}
    
    context = {
        'chef': chef,
        'recipes': recipes,
        'featured_recipes': featured_recipes,
        'recipe_count': recipe_count,
        'categorized_recipes': categorized_recipes,
        'chef_name': 'Alex Molina'
    }
    
    return render(request, 'alex.html', context)

def chef_wade_view(request):
    try:
        wade_user = User.objects.get(username='wade-alexandander')
        chef = Chef.objects.get(user=wade_user)

        recipes = Recipe.objects.filter(author=wade_user).order_by('-created_at')
        featured_recipes = recipes.filter(is_featured=True)[:3]
        recipe_count = recipes.count()
        
        # Get top rated recipes
        top_recipes = recipes.annotate(
            avg_rating=Avg('ratings__rating')
        ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:5]
        
    except (User.DoesNotExist, Chef.DoesNotExist):
        chef = None
        recipes = []
        featured_recipes = []
        top_recipes = []
        recipe_count = 0
    
    context = {
        'chef': chef,
        'recipes': recipes,
        'featured_recipes': featured_recipes,
        'top_recipes': top_recipes,
        'recipe_count': recipe_count,
        'chef_name': 'Wade Alexander'
    }
    
    return render(request, 'wade.html', context)

def chef_couple_view(request):
    try:
        nathan_user = User.objects.filter(username='Nate').first()

        couple_chef = Chef.objects.filter(user=nathan_user).first() if nathan_user else None
        
        if nathan_user:
            recipes = Recipe.objects.filter(author=nathan_user).order_by('-created_at')
            featured_recipes = recipes.filter(is_featured=True)[:3]
            recipe_count = recipes.count()
            date_night_recipes = recipes.filter(
                Q(title__icontains='date night') | 
                Q(description__icontains='date night') |
                Q(category__name__icontains='date')
            )[:5]
        else:
            recipes = []
            featured_recipes = []
            date_night_recipes = []
            recipe_count = 0
    except:
        recipes = []
        featured_recipes = []
        date_night_recipes = []
        recipe_count = 0
        couple_chef = None
    
    context = {
        'chef': couple_chef,
        'recipes': recipes,
        'featured_recipes': featured_recipes,
        'date_night_recipes': date_night_recipes,
        'recipe_count': recipe_count,
        'chef_name': 'Nathan & Jade'
    }
    
    return render(request, 'nate.html', context)

def chef_amanda_view(request):
    try:
  
        amanda_user = User.objects.filter(username='amanda-molina').first()
        chef = Chef.objects.filter(user=amanda_user).first() if amanda_user else None
        
        if amanda_user:

            recipes = Recipe.objects.filter(author=amanda_user).order_by('-created_at')
            featured_recipes = recipes.filter(is_featured=True)[:3]
            recipe_count = recipes.count()
            
            family_favorites = recipes.annotate(
                avg_rating=Avg('ratings__rating')
            ).filter(avg_rating__gte=4.0)[:5]
            
            recipe_categories = {}
            for recipe in recipes:
                category_name = recipe.category.name
                if category_name not in recipe_categories:
                    recipe_categories[category_name] = []
                recipe_categories[category_name].append(recipe)
        else:
            recipes = []
            featured_recipes = []
            recipe_count = 0
            family_favorites = []
            recipe_categories = {}
    except:
        chef = None
        recipes = []
        featured_recipes = []
        recipe_count = 0
        family_favorites = []
        recipe_categories = {}
    
    context = {
        'chef': chef,
        'recipes': recipes,
        'featured_recipes': featured_recipes,
        'family_favorites': family_favorites,
        'recipe_categories': recipe_categories,
        'recipe_count': recipe_count,
        'chef_name': 'Amanda'
    }
    
    return render(request, 'amanda.html', context)