from django.urls import path
from . import views

urlpatterns = [
    path('', views.TabelaFreteListView.as_view(), name='tabela_frete_list'),
    path('nova/', views.TabelaFreteCreateView.as_view(), name='tabela_frete_create'),
    path('<int:pk>/', views.TabelaFreteDetailView.as_view(), name='tabela_frete_detail'),
    path('<int:pk>/editar/', views.TabelaFreteUpdateView.as_view(), name='tabela_frete_update'),
    path('<int:pk>/excluir/', views.TabelaFreteDeleteView.as_view(), name='tabela_frete_delete'),
]
