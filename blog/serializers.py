from django.contrib.auth.models import User
from user_account.models import CustomUser
from rest_framework import serializers
from .models import Recipe, Category, Review, Favourite
from tinymce.models import HTMLField

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']
        

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    recipe = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ["id", 'user', 'recipe', 'comment', 'rating', 'created_date']


class AddRecipeSerializer(serializers.ModelSerializer):
    ingredients = HTMLField()
    instructions = HTMLField()
    # category_id = serializers.IntegerField(write_only=True)
    # category = CategorySerializer()  # Use the full category serializer
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    reviews = ReviewSerializer(many=True, read_only=True, source='recipe_review')
    is_favourited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'category', 'image', 'prep_time', 'cook_time', 
                  'servings', 'ingredients', 'instructions', 'created_at', 'updated_at', 'reviews', 'is_favourited']

    def get_is_favourited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Favourite.objects.filter(user=user, recipe=obj).exists()
        return False
    
    # def create(self, validated_data):
    #     category_id = validated_data.pop('category_id')
    #     category = Category.objects.get(id=category_id)
    #     recipe = Recipe.objects.create(category=category, **validated_data)
    #     return recipe


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "password",)
