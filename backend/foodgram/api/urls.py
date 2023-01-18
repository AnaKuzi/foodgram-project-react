from django.urls import include, path
from rest_framework import routers

from .views import (APIToken, BlacklistRefreshView, FavoriteViewSet,
                    FollowView, IngredientViewSet, RecipeViewSet,
                    ShoppingCartViewSet, TagViewSet, UserViewSet)

app_name = 'api'

router = routers.DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
      path('users/<int:user_id>/subscribe/',
           FollowView.as_view(), name='follow'),
      path('recipes/<int:recipe_id>/favorite/',
           FavoriteViewSet.as_view(), name='favorite'),
      path('recipes/<int:recipe_id>/shopping_cart/',
           ShoppingCartViewSet.as_view(), name='cart'),
      path('', include(router.urls)),
      path('auth/token/login/', APIToken.as_view(), name='token'),
      path('auth/token/logout/',
           BlacklistRefreshView.as_view(), name='logout'),
]
