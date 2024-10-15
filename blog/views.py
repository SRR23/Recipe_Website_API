from django.shortcuts import render
from user_account.models import CustomUser
from rest_framework import viewsets, pagination, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Recipe, Category, Favourite
from .serializers import AddRecipeSerializer, UserProfileUpdateSerializer, CategorySerializer, ReviewSerializer
from django.db.models import Q
from rest_framework.filters import SearchFilter

class PaginationView(pagination.PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 100


# Home view - Displays the latest 3 recipes with N+1 optimization
class HomeView(ListAPIView):
    queryset = Recipe.objects.select_related('category').prefetch_related('recipe_review__user').order_by('-created_at')[:3]
    serializer_class = AddRecipeSerializer


# List all categories
class CategoryListView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    
class SelectCategoryView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# List all recipes with filtering and search functionality
class RecipeListView(ListAPIView):
    queryset = Recipe.objects.select_related('category').prefetch_related('recipe_review__user').order_by('-created_at')
    # queryset = Recipe.objects.all().order_by('-created_at')  # Fetch all recipes, ordered by creation date
    serializer_class = AddRecipeSerializer
    pagination_class = PaginationView  # Use the custom pagination class



# Recipe detail view - Optimized for review relations
class RecipeDetailView(RetrieveAPIView):
    queryset = Recipe.objects.select_related('category', 'author') \
                             .prefetch_related('recipe_review')
    serializer_class = AddRecipeSerializer
    lookup_field = 'slug'
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReviewSerializer
        return AddRecipeSerializer

    def perform_create(self, serializer):
        recipe = self.get_object()
        serializer.save(user=self.request.user, recipe=recipe)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
# RecipeViewSet for creating and managing recipes by the logged-in user
class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = AddRecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Recipe.objects.filter(author=self.request.user) \
                             .select_related('category', 'author') \
                             .prefetch_related('recipe_review')

    def perform_create(self, serializer):
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
        favourites = Recipe.objects.filter(favourited_by__user=user) \
                                   .select_related('category', 'author') \
                                   .prefetch_related('recipe_review')
        serializer = AddRecipeSerializer(favourites, many=True, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, slug):
        user = request.user
        try:
            recipe = Recipe.objects.get(slug=slug)
        except Recipe.DoesNotExist:
            return Response({"detail": "Recipe not found."}, status=status.HTTP_404_NOT_FOUND)

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
        return CustomUser.objects.filter(id=self.request.user.id)

    def perform_update(self, serializer):
        serializer.save()  # No need to pass user here since the serializer handles it




class CategoryFilterView(ListAPIView):
    serializer_class = AddRecipeSerializer

    def get_queryset(self):
        # Get the category ID from query params
        category_id = self.request.query_params.get('category', None)
        
        # If no category_id is provided, return an empty queryset
        if category_id is None:
            return Recipe.objects.none()

        # Filter the recipes by category ID
        queryset = Recipe.objects.select_related('category') \
                                 .prefetch_related(
                                     'recipe_review__user'  # Prefetch reviews and the users who created them
                                 ) \
                                 .filter(category__id=category_id) \
                                 .order_by('-created_at')
        
        return queryset
    


class RecipeSearchView(ListAPIView):
    
    serializer_class = AddRecipeSerializer
    filter_backends = [SearchFilter]


    def get_queryset(self):
        queryset = Recipe.objects.select_related('category').prefetch_related('recipe_review__user')
        
        search_query = self.request.query_params.get('search', None)
        if search_query:
            # Use Q objects to search across related fields
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(ingredients__icontains=search_query) |
                Q(recipe_review__user__username__icontains=search_query)  # Adjust the field name based on your user model
            ).distinct()  # Use distinct to avoid duplicates due to join operations
        
        return queryset
