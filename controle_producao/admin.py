from django.contrib import admin
from .models import Componente

@admin.register(Componente)
class ComponenteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco', 'ativo', 'atualizado_em')
    search_fields = ('nome',)
    list_filter = ('ativo',)
    list_editable = ('preco', 'ativo')