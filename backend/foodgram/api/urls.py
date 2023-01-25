from django.urls import include, path
from rest_framework import routers

from .views import (APIToken, BlacklistRefresh, FavoriteView, FollowView,
                    IngredientViewSet, RecipeViewSet, ShoppingCartView,
                    TagViewSet, UserViewSet)

app_name = 'api'

router = routers.DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
     path('auth/token/login/', APIToken.as_view(), name='token'),
     path('auth/token/logout/',
          BlacklistRefresh.as_view(), name='logout'),
     path('users/<int:user_id>/subscribe/',
          FollowView.as_view(), name='follow'),
     path('recipes/<int:recipe_id>/favorite/',
          FavoriteView.as_view(), name='favorite'),
     path('recipes/<int:recipe_id>/shopping_cart/',
          ShoppingCartView.as_view(), name='cart'),
     path('', include(router.urls)),
]
