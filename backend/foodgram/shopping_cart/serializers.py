from rest_framework import exceptions, serializers

from shopping_cart.models import ShoppingCart


class ShoppingCartSerializer(serializers.ModelSerializer):
    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')

        if ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
            raise exceptions.ValidationError(
                detail='Пользователь уже добавил ингредиеты в список покупок'
            )
        return data

    def to_representation(self, instance):
        return {
            'id': instance.recipe.id,
            'name': instance.recipe.name,
            'image': str(instance.recipe.image),
            'cooking_time': instance.recipe.cooking_time,
        }

    class Meta:
        model = ShoppingCart
        fields = '__all__'
