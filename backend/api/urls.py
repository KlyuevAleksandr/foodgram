from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, IngViewSet, TagViewSet
from .recipes_views import RecipeViewSet

router = DefaultRouter()
router.register("ingredients", IngViewSet, basename="ingredients")
router.register("users", UserViewSet, basename="users")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("tags", TagViewSet, basename="tags")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include('djoser.urls.authtoken')),
]
