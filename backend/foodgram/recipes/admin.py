from django.contrib import admin

from .models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                     RecipeTag, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_filter = ('name',)
    list_display = ('name', 'measurement_unit')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    raw_id_fields = ('ingredient',)
    extra = 0


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag
    raw_id_fields = ('tag',)
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    list_select_related = True
    search_fields = ('name',)
    inlines = (
        RecipeIngredientInline,
        RecipeTagInline,
    )

    def change_view(self, request, object_id, form_url='', extra_content=None):
        in_favorites_count = FavoriteRecipe.objects.filter(
            recipe=object_id
        ).count()
        context = {'in_favorites_count': in_favorites_count}
        return super(RecipeAdmin, self).change_view(
            request, object_id, form_url, context
        )


admin.site.register(Tag)
admin.site.register(RecipeTag)
admin.site.register(RecipeIngredient)
admin.site.register(FavoriteRecipe)
