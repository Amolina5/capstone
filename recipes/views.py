from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Avg
from .models import Recipe, Category, RecipeRating, Chef
from .forms import RecipeForm, RatingForm

def home_view(request):
    """View for the homepage"""
    # Get featured recipes for the homepage carousel
    featured_recipes = Recipe.objects.filter(is_featured=True)[:6]
    
    # Get the latest recipes for the recent additions section
    latest_recipes = Recipe.objects.order_by('-created_at')[:6]
    
    # Get all categories for the category navigation
    categories = Category.objects.all()
    
    # Get featured chefs
    featured_chefs = Chef.objects.all()[:3]
    
    context = {
        'featured_recipes': featured_recipes,
        'latest_recipes': latest_recipes,
        'categories': categories,
        'featured_chefs': featured_chefs,
    }
    return render(request, 'pages/home.html', context)

def recipe_list(request):
    """View for listing all recipes with filtering options"""
    # Get all recipes
    recipes = Recipe.objects.all()
    
    # Get all categories for the filter sidebar
    categories = Category.objects.all()
    
    # Filter by category if requested
    category_slug = request.GET.get('category')
    if category_slug:
        recipes = recipes.filter(category__slug=category_slug)
    
    # Filter by difficulty if requested
    difficulty = request.GET.get('difficulty')
    if difficulty:
        recipes = recipes.filter(difficulty=difficulty)
    
    # Filter by chef if requested
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
    """View for displaying a single recipe with ratings"""
    # Get the requested recipe
    recipe = get_object_or_404(Recipe, slug=slug)
    
    # Get the rating form for logged-in users
    rating_form = RatingForm()
    
    # Check if the user has already rated this recipe
    user_rating = None
    if request.user.is_authenticated:
        user_rating = RecipeRating.objects.filter(recipe=recipe, user=request.user).first()
    
    # Get related recipes (same category or by same chef)
    related_by_category = Recipe.objects.filter(category=recipe.category).exclude(id=recipe.id)[:3]
    related_by_chef = Recipe.objects.filter(author=recipe.author).exclude(id=recipe.id)[:3]
    
    # Try to get the chef profile of the recipe author
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
    return render(request, 'recipes/recipe_detail.html', context)

def category_detail(request, slug):
    """View for displaying all recipes in a specific category"""
    # Get the requested category
    category = get_object_or_404(Category, slug=slug)
    
    # Get all recipes in this category
    recipes = Recipe.objects.filter(category=category)
    
    context = {
        'category': category,
        'recipes': recipes,
    }
    return render(request, 'recipes/category_detail.html', context)

@login_required
def recipe_add(request):
    """View for adding a new recipe (requires login)"""
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
    """View for editing an existing recipe (requires login and ownership)"""
    # Get the recipe to edit
    recipe = get_object_or_404(Recipe, slug=slug)
    
    # Check if the current user is the author
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
    """View for deleting a recipe (requires login and ownership)"""
    # Get the recipe to delete
    recipe = get_object_or_404(Recipe, slug=slug)
    
    # Check if the current user is the author
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
    """View for rating a recipe (requires login)"""
    # Get the recipe to rate
    recipe = get_object_or_404(Recipe, slug=slug)
    
    if request.method == 'POST':
        # Create or update the user's rating
        rating, created = RecipeRating.objects.get_or_create(
            recipe=recipe,
            user=request.user,
            defaults={
                'rating': request.POST.get('rating'),
                'comment': request.POST.get('comment', '')
            }
        )
        
        # If the rating already existed, update it
        if not created:
            rating.rating = request.POST.get('rating')
            rating.comment = request.POST.get('comment', '')
            rating.save()
        
        messages.success(request, 'Thank you for rating this recipe!')
        
    return redirect('recipes:recipe_detail', slug=slug)

def chefs_view(request):
    """View for the main chefs listing page"""
    # Get all chefs
    chefs = Chef.objects.all()
    
    # Enhance each chef with recipe information
    for chef in chefs:
        if chef.user:
            # Get the featured recipe for this chef
            chef.featured_recipe = Recipe.objects.filter(
                author=chef.user, 
                is_featured=True
            ).first()
            
            # Count recipes by this chef
            chef.recipe_count = Recipe.objects.filter(
                author=chef.user
            ).count()
            
            # Get average rating of recipes by this chef
            chef.avg_rating = Recipe.objects.filter(
                author=chef.user
            ).annotate(
                avg_rating=Avg('ratings__rating')
            ).aggregate(Avg('avg_rating'))['avg_rating__avg'] or 0
        else:
            chef.featured_recipe = None
            chef.recipe_count = 0
            chef.avg_rating = 0
    
    context = {
        'chefs': chefs
    }
    
    # THIS WAS MISSING: Return an HttpResponse
    return render(request, 'pages/chefs.html', context)

def recipes_view(request):
    """View for the main recipes page, organized by chef"""
    # Get all chefs that have user accounts
    chefs = Chef.objects.exclude(user__isnull=True)
    
    # Get all categories for filtering
    categories = Category.objects.all()
    
    # Filter by category if requested
    category_slug = request.GET.get('category', '')  # Default to empty string
    category_filter = None
    
    if category_slug and category_slug != '':
        try:
            category_filter = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            # If category doesn't exist, don't filter
            pass
    
    # Prepare chef data for the template
    chefs_with_recipes = []
    
    for chef in chefs:
        # Get recipes by this chef
        chef_recipes = Recipe.objects.filter(author=chef.user)
        
        # Apply category filter if selected
        if category_filter:
            chef_recipes = chef_recipes.filter(category=category_filter)
        
        # Store recipes with the chef regardless of count
        chef.recipes = chef_recipes.order_by('-created_at')[:6]
        chef.recipe_count = chef_recipes.count()
        
        # Always include the chef, even if they have no recipes in this category
        chefs_with_recipes.append(chef)
    
    # Get total recipe count
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

# Chef-specific views follow below

def chef_detail_view(request, slug):
    """Generic view for displaying any chef's profile by slug"""
    # Get the chef by slug
    chef = get_object_or_404(Chef, slug=slug)
    
    # Get recipes by this chef
    if chef.user:
        recipes = Recipe.objects.filter(author=chef.user).order_by('-created_at')
        featured_recipes = recipes.filter(is_featured=True)[:3]
        recipe_count = recipes.count()
        
        # Get recipe statistics
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
    
    # Use the generic chef_detail.html template if you want to create one
    # Otherwise, you'd need to map specific slugs to specific templates
    return render(request, 'recipes/chef_detail.html', context)

def chef_cameron_view(request):
    """View for Cameron Quinn's chef page"""
    try:
        # Get Cameron's user and chef profile
        cameron_user = User.objects.get(username='cameron-quinn')
        chef = Chef.objects.get(user=cameron_user)
        
        # Get recipes by Cameron
        recipes = Recipe.objects.filter(author=cameron_user).order_by('-created_at')
        featured_recipes = recipes.filter(is_featured=True)[:3]
        recipe_count = recipes.count()
        
        # Get recent recipes
        recent_recipes = recipes[:5]
        
    except (User.DoesNotExist, Chef.DoesNotExist):
        # Fallback if user or chef doesn't exist
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
    """View for Alex Molina's chef page"""
    try:
        # Get Alex's user and chef profile
        alex_user = User.objects.get(username='alex-molina')
        chef = Chef.objects.get(user=alex_user)
        
        # Get recipes by Alex
        recipes = Recipe.objects.filter(author=alex_user).order_by('-created_at')
        featured_recipes = recipes.filter(is_featured=True)[:3]
        recipe_count = recipes.count()
        
        # Get recipes by category
        categorized_recipes = {}
        for recipe in recipes:
            category_name = recipe.category.name
            if category_name not in categorized_recipes:
                categorized_recipes[category_name] = []
            categorized_recipes[category_name].append(recipe)
        
    except (User.DoesNotExist, Chef.DoesNotExist):
        # Fallback if user or chef doesn't exist
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
    """View for Wade Alexander's chef page"""
    try:
        # Get Wade's user and chef profile
        wade_user = User.objects.get(username='wade-alexandander')
        chef = Chef.objects.get(user=wade_user)
        
        # Get recipes by Wade
        recipes = Recipe.objects.filter(author=wade_user).order_by('-created_at')
        featured_recipes = recipes.filter(is_featured=True)[:3]
        recipe_count = recipes.count()
        
        # Get top rated recipes
        top_recipes = recipes.annotate(
            avg_rating=Avg('ratings__rating')
        ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:5]
        
    except (User.DoesNotExist, Chef.DoesNotExist):
        # Fallback if user or chef doesn't exist
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
    """View for Nathan & Jade's couples cooking page"""
    try:
        # Get both users
        nathan_user = User.objects.filter(username='nathan-jambo-jade-jambo').first()
        # Since we've created a single user for the couple, we don't need jade_user
        
        # Get chef profile
        couple_chef = Chef.objects.filter(user=nathan_user).first() if nathan_user else None
        
        # Get recipes by the couple
        if nathan_user:
            recipes = Recipe.objects.filter(author=nathan_user).order_by('-created_at')
            featured_recipes = recipes.filter(is_featured=True)[:3]
            recipe_count = recipes.count()
            
            # Get "date night" recipes - could be based on a specific category or tag
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
    """View for Amanda's Family Cookbook page"""
    try:
        # Get Amanda's user and chef profile
        amanda_user = User.objects.filter(username='amanda-molina').first()
        chef = Chef.objects.filter(user=amanda_user).first() if amanda_user else None
        
        if amanda_user:
            # Get all of Amanda's recipes
            recipes = Recipe.objects.filter(author=amanda_user).order_by('-created_at')
            featured_recipes = recipes.filter(is_featured=True)[:3]
            recipe_count = recipes.count()
            
            # Get family favorites - could be based on a specific tag or high ratings
            family_favorites = recipes.annotate(
                avg_rating=Avg('ratings__rating')
            ).filter(avg_rating__gte=4.0)[:5]
            
            # Group recipes by category for the family cookbook
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