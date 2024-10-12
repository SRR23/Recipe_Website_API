from django.contrib.auth.models import User
from user_account.models import CustomUser
from rest_framework import serializers
from .models import Recipe, Category, Review, Favourite
from tinymce.models import HTMLField
# from .models import Author

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']  # You can include other fields as needed


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # To show the username
    recipe = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Review
        fields = ["id", 'user', 'recipe', 'comment', 'rating', 'created_date']
        

class AddRecipeSerializer(serializers.ModelSerializer):
    ingredients = HTMLField()
    instructions = HTMLField()
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())  # For this we can sent category id in postman
    # category = CategorySerializer()
    reviews = ReviewSerializer(many=True, read_only=True, source='recipe_review')
    is_favourited = serializers.BooleanField(default=False) 
    
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'category', 'image', 'prep_time', 'cook_time', 
                  'servings', 'ingredients', 'instructions', 'created_at', 'updated_at', 'reviews', 'is_favourited']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.context['request'].user

        # Check if the user is authenticated before trying to query the favourite status
        if user.is_authenticated:
            data['is_favourited'] = Favourite.objects.filter(user=user, recipe=instance).exists()
        else:
            data['is_favourited'] = False  # If the user is anonymous, set to False

        return data


class UserProfileUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "password", )
