from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProdutoViewSet, GrupoCanaisViewSet, CanalVendaViewSet

router = DefaultRouter()
router.register(r'produtos', ProdutoViewSet, basename='produto-api')
router.register(r'grupos', GrupoCanaisViewSet, basename='grupo-api')
router.register(r'canais', CanalVendaViewSet, basename='canal-api')

urlpatterns = [
    path('', include(router.urls)),
]
