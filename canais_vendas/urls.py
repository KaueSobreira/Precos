from django.urls import path
from . import views

urlpatterns = [
    # Canais de Venda
    path('', views.CanalListView.as_view(), name='canal_list'),
    path('novo/', views.CanalCreateView.as_view(), name='canal_create'),
    path('<int:pk>/', views.CanalDetailView.as_view(), name='canal_detail'),
    path('<int:pk>/editar/', views.CanalUpdateView.as_view(), name='canal_update'),
    path('<int:pk>/excluir/', views.CanalDeleteView.as_view(), name='canal_delete'),

    # Tabelas de Frete
    path('frete/', views.TabelaFreteListView.as_view(), name='tabela_frete_list'),
    path('frete/nova/', views.TabelaFreteCreateView.as_view(), name='tabela_frete_create'),
    path('frete/<int:pk>/', views.TabelaFreteDetailView.as_view(), name='tabela_frete_detail'),
    path('frete/<int:pk>/editar/', views.TabelaFreteUpdateView.as_view(), name='tabela_frete_update'),
    path('frete/<int:pk>/excluir/', views.TabelaFreteDeleteView.as_view(), name='tabela_frete_delete'),
    path('frete/<int:tabela_pk>/regras/', views.regras_frete_edit, name='regras_frete_edit'),
]
