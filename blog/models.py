from django.db import models
from django.contrib.auth.models import User
from user_account.models import CustomUser
from django.utils.text import slugify
from .slug import generate_unique_slug
from tinymce.models import HTMLField
from PIL import Image
# Create your models here.

class Category(models.Model):
    title=models.CharField(max_length=150, unique=True)
    slug=models.SlugField(null=True, blank=True)
    created_date=models.DateField(auto_now_add=True)
    
    def __str__(self) -> str:
        return self.title
    
    def save(self,*args,**kwargs):
        self.slug=slugify(self.title)
        super().save(*args,**kwargs)
        
        
class Recipe(models.Model):
    author = models.ForeignKey(CustomUser, related_name='user_recipe', on_delete=models.CASCADE)
    category = models.ForeignKey(Category,related_name='category_recipe',on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    instructions = HTMLField()
    ingredients = HTMLField()  # You can also normalize this with an Ingredient model if you want.
    prep_time = models.IntegerField(help_text="Time in minutes")
    cook_time = models.IntegerField(help_text="Time in minutes")
    servings = models.IntegerField()
    image = models.ImageField(upload_to='recipe_images/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug=models.SlugField(null=True, blank=True)
    
    
    def __str__(self) -> str:
        return self.title
    
    def save(self, *args, **kwargs):
        # Check if the instance is being updated (already exists in the database)
        updating = self.pk is not None

        # Generate slug if not already provided
        if not self.slug:
            self.slug = slugify(self.title)

        # Call the original save method to save the object
        super().save(*args, **kwargs)

        # Resize the image after saving it
        if self.image:
            img_path = self.image.path
            img = Image.open(img_path)

            # Resize the image to the specified size (width: 330px, height: 285px)
            output_size = (330, 285)
            img = img.resize(output_size)
            img.save(img_path)
            
    # def save(self, *args, **kwargs):
    #     # Check if the instance is being updated (already exists in the database)
    #     updating = self.pk is not None
        
    #     # Update slug based on whether it's a new or existing instance
    #     if updating:
    #         self.slug = generate_unique_slug(self, self.title, update=True)
    #     else:
    #         self.slug = generate_unique_slug(self, self.title)
        
    #     # Call the original save method
    #     super().save(*args, **kwargs)


class Review(models.Model):
    user = models.ForeignKey(CustomUser,related_name='user_review',on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,related_name='recipe_review',on_delete=models.CASCADE)
    comment = models.TextField(max_length=250)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)],null=True)
    created_date = models.DateField(auto_now_add=True)
    
    def __str__(self) -> str:
        return self.comment


class Favourite(models.Model):
    user = models.ForeignKey(CustomUser, related_name='favourites', on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='favourited_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} favorited {self.recipe.title}"


    
