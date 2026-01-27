from django.urls import path
from . import views

urlpatterns = [
    # Canais de Venda
    path('', views.CanalListView.as_view(), name='canal_list'),
    path('novo/', views.CanalCreateView.as_view(), name='canal_create'),
    path('<int:pk>/', views.CanalDetailView.as_view(), name='canal_detail'),
    path('<int:pk>/editar/', views.CanalUpdateView.as_view(), name='canal_update'),
    path('<int:pk>/excluir/', views.CanalDeleteView.as_view(), name='canal_delete'),
]