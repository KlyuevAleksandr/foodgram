from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .views import recipe_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("api.urls")),
    path('recipes/<int:pk>/', recipe_view, name='redirect_recipe'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
