from django.urls import path
from . import views

urlpatterns = [
    # Tabela Frete
    path('', views.TabelaFreteListView.as_view(), name='tabela_frete_list'),
    path('nova/', views.TabelaFreteCreateView.as_view(), name='tabela_frete_create'),
    path('<int:pk>/', views.TabelaFreteDetailView.as_view(), name='tabela_frete_detail'),
    path('<int:pk>/editar/', views.TabelaFreteUpdateView.as_view(), name='tabela_frete_update'),
    path('<int:pk>/excluir/', views.TabelaFreteDeleteView.as_view(), name='tabela_frete_delete'),

    # Regras Matriz
    path('<int:tabela_pk>/regras-matriz/bulk/', views.RegrasMatrizBulkEditView.as_view(), name='regras_matriz_bulk_edit'),
    path('<int:tabela_pk>/regras-matriz/importar/', views.RegrasMatrizImportView.as_view(), name='regras_matriz_import'),
    path('<int:tabela_pk>/regras-matriz/modelo/', views.RegrasMatrizTemplateView.as_view(), name='regras_matriz_template'),
    path('<int:tabela_pk>/regras-matriz/nova/', views.RegraMatrizCreateView.as_view(), name='regra_matriz_create'),
    path('regras-matriz/<int:pk>/editar/', views.RegraMatrizUpdateView.as_view(), name='regra_matriz_update'),
    path('regras-matriz/<int:pk>/excluir/', views.RegraMatrizDeleteView.as_view(), name='regra_matriz_delete'),

    # Regras Simples
    path('<int:tabela_pk>/regras-simples/nova/', views.RegraSimplesCreateView.as_view(), name='regra_simples_create'),
    path('<int:tabela_pk>/regras-simples/importar/', views.RegrasSimplesImportView.as_view(), name='regras_simples_import'),
    path('<int:tabela_pk>/regras-simples/modelo/', views.RegrasSimplesTemplateView.as_view(), name='regras_simples_template'),
    path('regras-simples/<int:pk>/editar/', views.RegraSimplesUpdateView.as_view(), name='regra_simples_update'),
    path('regras-simples/<int:pk>/excluir/', views.RegraSimplesDeleteView.as_view(), name='regra_simples_delete'),

    # Descontos
    path('<int:tabela_pk>/descontos/novo/', views.DescontoCreateView.as_view(), name='desconto_create'),
    path('descontos/<int:pk>/editar/', views.DescontoUpdateView.as_view(), name='desconto_update'),
    path('descontos/<int:pk>/excluir/', views.DescontoDeleteView.as_view(), name='desconto_delete'),
]