from django.contrib.auth import get_user_model
from django.db import models

from recipes.models import Recipe

User = get_user_model()


class ShoppingCart(models.Model):
    """Модель списка покупок"""
    user = models.ForeignKey(User,
                             related_name='shopping_cart',
                             on_delete=models.CASCADE,
                             verbose_name='Cart_user')
    recipe = models.ForeignKey(Recipe,
                               related_name='shopping_cart',
                               on_delete=models.CASCADE,
                               verbose_name='Cart_recipe')

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='shopping_cart_user_recipe_unique',
            ),
        ]

    def __str__(self):
        return (f'Пользователь {self.user} добавил',
                f'в корзину рецепт {self.recipe}')
