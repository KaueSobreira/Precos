from django.urls import path
from . import views

urlpatterns = [
    path('', views.GrupoListView.as_view(), name='grupo_list'),
    path('novo/', views.GrupoCreateView.as_view(), name='grupo_create'),
    path('<int:pk>/', views.GrupoDetailView.as_view(), name='grupo_detail'),
    path('<int:pk>/editar/', views.GrupoUpdateView.as_view(), name='grupo_update'),
    path('<int:pk>/excluir/', views.GrupoDeleteView.as_view(), name='grupo_delete'),
]
