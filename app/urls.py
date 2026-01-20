from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Apps do sistema
    path('', include('produtos.urls')),
    path('grupos/', include('grupo_vendas.urls')),
    path('canais/', include('canais_vendas.urls')),
    path('fretes/', include('tabela_frete.urls')),
]
