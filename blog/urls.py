from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


# Create a router and register the viewset with it
recipe_router  = DefaultRouter()
recipe_router.register(r'my-recipes', views.RecipeViewSet, basename='recipe')
recipe_router.register(r'my-profile', views.UserProfileUpdateView, basename='profile')


# Include the router-generated URLs in your project’s URL patterns
urlpatterns = [
    path('home/', views.HomeView.as_view(), name='home'),  # API home page
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('ctg/', views.SelectCategoryView.as_view(), name='ctg-list'),
    path('recipes/', views.RecipeListView.as_view(), name='recipe-list'),  # API home page
    path('recipe-detail/<str:slug>/', views.RecipeDetailView.as_view(), name='recipe-detail'),
    path('add-favourite/<str:slug>/', views.AddFavouriteView.as_view(), name='toggle_favourite'),
    path('favourite-list/', views.FavouriteListView.as_view(), name='favourite_list'),
    path('favourite-list/<str:slug>/', views.FavouriteListView.as_view(), name='favourite_list'), # for delete
    path('filter/', views.CategoryFilterView.as_view(), name='recipe-filter'),
    path('search/', views.RecipeSearchView.as_view(), name='recipe-search'),
    path('', include(recipe_router.urls)),
]