from django.contrib import admin
from .models import TabelaFrete, RegraFreteMatriz, DescontoNotaVendedor, TabelaTaxa, RegraTaxa

class RegraFreteMatrizInline(admin.TabularInline):
    model = RegraFreteMatriz
    extra = 1
    fields = ['ordem', 'peso_inicio', 'peso_fim', 'preco_inicio', 'preco_fim', 'valor_frete', 'ativo']
    ordering = ['ordem', 'peso_inicio', 'preco_inicio']

class DescontoNotaVendedorInline(admin.TabularInline):
    model = DescontoNotaVendedor
    extra = 1

@admin.register(TabelaFrete)
class TabelaFreteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'ativo', 'atualizado_em']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome']
    
    def get_inlines(self, request, obj=None):
        inlines = []
        if obj and obj.tipo == 'matriz':
            inlines.append(RegraFreteMatrizInline)
        # Se houver outro tipo (ex: simples) adicionaria aqui
        
        if obj and obj.suporta_nota_vendedor:
            inlines.append(DescontoNotaVendedorInline)
        return inlines

@admin.register(RegraFreteMatriz)
class RegraFreteMatrizAdmin(admin.ModelAdmin):
    list_display = ['tabela', 'ordem', 'peso_inicio', 'peso_fim', 'preco_inicio', 'preco_fim', 'valor_frete']
    list_filter = ['tabela']
    ordering = ['tabela', 'ordem']

class RegraTaxaInline(admin.TabularInline):
    model = RegraTaxa
    extra = 1
    fields = ['preco_inicio', 'preco_fim', 'valor_taxa', 'ativo']
    ordering = ['preco_inicio']

@admin.register(TabelaTaxa)
class TabelaTaxaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'atualizado_em']
    inlines = [RegraTaxaInline]