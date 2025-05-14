# recipes/forms.py
from django import forms
from .models import Recipe, RecipeRating
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = [
            'title', 'category', 'description', 'ingredients', 
            'instructions', 'prep_time', 'cook_time', 'servings', 
            'difficulty', 'image', 'is_featured'
        ]
        widgets = {
            'ingredients': forms.Textarea(attrs={'rows': 10, 'placeholder': 'Enter each ingredient on a new line'}),
            'instructions': forms.Textarea(attrs={'rows': 15, 'placeholder': 'Enter step-by-step instructions'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'  
        self.helper.add_input(Submit('submit', 'Save Recipe'))

class RatingForm(forms.ModelForm):
    class Meta:
        model = RecipeRating
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Share your thoughts on this recipe'}),
        }