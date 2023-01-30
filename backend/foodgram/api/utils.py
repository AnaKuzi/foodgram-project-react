from django.shortcuts import get_object_or_404
from recipes.models import Ingredient, RecipeIngredient, RecipeTag, Tag


def add_recipe_tags_ingredients(tags, ingredients, recipe):
    """Метод для создания ингрединтов и тэгов в рецепте"""

    RecipeIngredient.objects.bulk_create(
        [RecipeIngredient(
            ingredient=get_object_or_404(Ingredient, id=ingredient['id']),
            recipe=recipe,
            amount=ingredient['amount']) for ingredient in ingredients])
    RecipeTag.objects.bulk_create(
        [RecipeTag(tag=get_object_or_404(Tag, id=tag),
                   recipe=recipe) for tag in tags])
