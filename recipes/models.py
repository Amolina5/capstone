# recipes/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Chef(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    specialty = models.CharField(max_length=100)
    bio = models.TextField()
    image = models.ImageField(upload_to='chefs/', blank=True, null=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chef_profile', null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_recipes(self):
        """Get all recipes by this chef"""
        if self.user:
            return self.user.recipes.all()
        return []
    
    def get_recipes_count(self):
        """Get the count of recipes by this chef"""
        if self.user:
            return self.user.recipes.count()
        return 0
    
    def get_featured_recipes(self):
        """Get featured recipes by this chef"""
        if self.user:
            return self.user.recipes.filter(is_featured=True)
        return []

class Recipe(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    ingredients = models.TextField()
    instructions = models.TextField()
    prep_time = models.PositiveIntegerField(help_text='Preparation time in minutes')
    cook_time = models.PositiveIntegerField(help_text='Cooking time in minutes')
    servings = models.PositiveIntegerField(default=4)
    difficulty = models.CharField(
        max_length=10, 
        choices=DIFFICULTY_CHOICES,
        default='medium'
    )
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='recipes')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @property
    def total_time(self):
        """Return the total time (prep + cook) in minutes"""
        return self.prep_time + self.cook_time
    
    @property
    def average_rating(self):
        """Calculate the average rating for this recipe"""
        ratings = self.ratings.all()
        if not ratings:
            return 0
        return sum(r.rating for r in ratings) / len(ratings)
    
    def get_chef(self):
        """Get the chef profile associated with this recipe's author"""
        try:
            return self.author.chef_profile
        except:
            return None

class RecipeRating(models.Model):
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('recipe', 'user')
    
    def __str__(self):
        return f"{self.user.username}'s rating for {self.recipe.title}"