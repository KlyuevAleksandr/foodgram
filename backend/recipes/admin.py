from django.contrib import admin
from django.utils.html import format_html
from .models import Tag, Ingredient, Recipe, RecipeIng, Favorite, ShoppingCart


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'slug')
    list_filter = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


class RecipeIngInline(admin.TabularInline):
    model = RecipeIng
    extra = 1
    min_num = 1
    verbose_name = "Ингредиент"
    verbose_name_plural = "Ингредиенты"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author', 'cooking_time',
        'get_ingredients', 'get_tags', 'get_image_preview'
    )
    list_display_links = ('id', 'name')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'author')
    filter_horizontal = ('tags',)
    inlines = (RecipeIngInline,)
    readonly_fields = ('get_image_preview',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('author', 'name', 'text', 'image', 'get_image_preview')
        }),
        ('Детали', {
            'fields': ('cooking_time', 'tags')
        }),
    )
    ordering = ('name',)

    def get_ingredients(self, obj):
        return ", ".join([ingredient.name for ingredient in obj.ingredients.all()])
    get_ingredients.short_description = 'Ингредиенты'

    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    get_tags.short_description = 'Теги'

    def get_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.image.url
            )
        return "Нет изображения"
    get_image_preview.short_description = 'Предпросмотр изображения'


@admin.register(RecipeIng)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_display_links = ('id', 'recipe')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe', 'ingredient')
    ordering = ('recipe',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
    ordering = ('user',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
    ordering = ('user',)