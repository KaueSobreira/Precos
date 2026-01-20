from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.home, name='home'),

    # Produtos
    path('produtos/', views.ProdutoListView.as_view(), name='produto_list'),
    path('produtos/novo/', views.ProdutoCreateView.as_view(), name='produto_create'),
    path('produtos/<int:pk>/', views.ProdutoDetailView.as_view(), name='produto_detail'),
    path('produtos/<int:pk>/editar/', views.ProdutoUpdateView.as_view(), name='produto_update'),
    path('produtos/<int:pk>/excluir/', views.ProdutoDeleteView.as_view(), name='produto_delete'),

    # Ficha Técnica
    path('produtos/<int:produto_pk>/ficha/', views.ficha_tecnica_edit, name='ficha_tecnica_edit'),

    # Títulos Secundários
    path('produtos/<int:produto_pk>/titulos/', views.titulos_edit, name='titulos_edit'),

    # Preços por Canal
    path('precos/', views.PrecoListView.as_view(), name='preco_list'),
    path('precos/<int:pk>/editar/', views.preco_edit, name='preco_edit'),
    path('produtos/<int:produto_pk>/precos/', views.produto_precos, name='produto_precos'),

    # Histórico
    path('historico/', views.HistoricoListView.as_view(), name='historico_list'),
    path('historico/<int:pk>/', views.HistoricoDetailView.as_view(), name='historico_detail'),
]
