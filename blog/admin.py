from django.contrib import admin
from .models import *
# Register your models here.

class RecipeAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ('title',)}
    
    
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ('title',)}
    


admin.site.register(Category, CategoryAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Review)
admin.site.register(Favourite)