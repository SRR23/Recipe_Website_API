from django.shortcuts import render
from user_account.models import CustomUser  # Import the CustomUser model
from rest_framework import viewsets, pagination, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from .models import Recipe, Category, Favourite
from .serializers import AddRecipeSerializer, UserProfileUpdateSerializer, CategorySerializer, ReviewSerializer


# Custom pagination class
class PaginationView(pagination.PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 100
    

# Home view - Displays the latest 3 recipes
class HomeView(ListAPIView):
    queryset = Recipe.objects.all().order_by('-created_at')[:3]  # Fetch the latest 3 recipes
    serializer_class = AddRecipeSerializer


# List all categories
class CategoryListView(ListAPIView):
    queryset = Category.objects.all()  # Fetch all categories
    serializer_class = CategorySerializer


# List all recipes with filtering and search functionality
class RecipeListView(ListAPIView):
    queryset = Recipe.objects.all().order_by('-created_at')  # Fetch all recipes, ordered by creation date
    serializer_class = AddRecipeSerializer
    filterset_fields = ['category', 'author']  # Filter recipes by category or author
    search_fields = ['title', 'instructions', 'ingredients']  # Search recipes by title, instructions, or ingredients
    pagination_class = PaginationView  # Use the custom pagination class


# Recipe detail view - Can also handle POST requests to submit reviews
class RecipeDetailView(RetrieveAPIView):
    queryset = Recipe.objects.all()  # Fetch all recipes
    serializer_class = AddRecipeSerializer
    lookup_field = 'slug'  # Use the 'slug' field for lookup
    permission_classes = [IsAuthenticatedOrReadOnly]  # Only authenticated users can submit reviews

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReviewSerializer  # Use ReviewSerializer for posting reviews
        return AddRecipeSerializer  # Use AddRecipeSerializer for retrieving recipe details

    def perform_create(self, serializer):
        # Save the review with the logged-in user and the specific recipe
        recipe = self.get_object()  # Get the specific recipe being reviewed
        serializer.save(user=self.request.user, recipe=recipe)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to submit a review for the recipe.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

# RecipeViewSet for creating and managing recipes by the logged-in user
class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = AddRecipeSerializer
    permission_classes = [IsAuthenticated]  # Require users to be authenticated

    def get_queryset(self):
        # Show only the recipes authored by the logged-in user
        return Recipe.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        # Save the recipe with the logged-in user as the author
        serializer.save(author=self.request.user)



class AddFavouriteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        user = request.user
        recipe = Recipe.objects.get(slug=slug)
        favourite, created = Favourite.objects.get_or_create(user=user, recipe=recipe)

        if not created:
            favourite.delete()
            return Response({"detail": "Recipe removed from favorites"}, status=status.HTTP_200_OK)
        return Response({"detail": "Recipe added to favorites"}, status=status.HTTP_201_CREATED)
    

class FavouriteListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Get all favorite recipes for the logged-in user
        favourites = Recipe.objects.filter(favourited_by__user=user)
        serializer = AddRecipeSerializer(favourites, many=True, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, slug):
        user = request.user
        # Try to fetch the recipe by its slug
        try:
            recipe = Recipe.objects.get(slug=slug)
        except Recipe.DoesNotExist:
            return Response({"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the recipe is in the user's favorite list
        favourite = Favourite.objects.filter(user=user, recipe=recipe).first()

        if favourite:
            favourite.delete()
            return Response({"detail": "Recipe removed from favorites."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Recipe not in favorites."}, status=status.HTTP_400_BAD_REQUEST)
    
    
# UserProfileUpdateView for updating the logged-in user's profile
class UserProfileUpdateView(viewsets.ModelViewSet):
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Allow the logged-in user to view their own profile
        return CustomUser.objects.filter(id=self.request.user.id)

    def perform_update(self, serializer):
        # Ensure the user cannot modify another user's profile
        serializer.save(user=self.request.user)
