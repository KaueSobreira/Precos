from django.urls import path
from . import views

urlpatterns = [
    # API
    path('api/buscar-componente/', views.buscar_componente_api, name='buscar_componente_api'),
    
    # CRUD
    path('', views.ComponenteListView.as_view(), name='componente_list'),
    path('novo/', views.ComponenteCreateView.as_view(), name='componente_create'),
    path('<int:pk>/editar/', views.ComponenteUpdateView.as_view(), name='componente_update'),
    path('<int:pk>/excluir/', views.ComponenteDeleteView.as_view(), name='componente_delete'),
]