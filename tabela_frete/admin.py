from django.contrib import admin
from .models import TabelaFrete, RegraFreteMatriz, RegraFreteSimples, DescontoNotaVendedor, TabelaTaxa, RegraTaxa

class RegraFreteMatrizInline(admin.TabularInline):
    model = RegraFreteMatriz
    extra = 1
    fields = ['ordem', 'peso_inicio', 'peso_fim', 'preco_inicio', 'preco_fim', 'valor_frete', 'ativo']
    ordering = ['ordem', 'peso_inicio', 'preco_inicio']

class RegraFreteSimplesInline(admin.TabularInline):
    model = RegraFreteSimples
    extra = 1
    fields = ['inicio', 'fim', 'valor_frete', 'ativo']
    ordering = ['inicio']
    verbose_name = "Regra Simples (Peso ou Preço)"
    verbose_name_plural = "Regras Simples (Peso ou Preço)"

class DescontoNotaVendedorInline(admin.TabularInline):
    model = DescontoNotaVendedor
    extra = 1

@admin.register(TabelaFrete)
class TabelaFreteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'ativo', 'atualizado_em']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['nome', 'tipo', 'descricao', 'ativo']
        }),
        ('Taxa Fixa Adicional', {
            'fields': ['adicionar_taxa_fixa', 'valor_taxa_fixa'],
            'description': 'Valor fixo adicionado ao frete APÓS o cálculo de descontos.'
        }),
        ('Descontos', {
            'fields': ['suporta_nota_vendedor'],
            'description': 'Habilite para configurar descontos baseados na nota do vendedor (1-5).'
        })
    ]

    def get_inlines(self, request, obj=None):
        inlines = []
        if obj:
            if obj.tipo == 'matriz':
                inlines.append(RegraFreteMatrizInline)
            elif obj.tipo in ['peso', 'preco']:
                inlines.append(RegraFreteSimplesInline)
        
        # Sempre mostra os descontos para facilitar o cadastro
        inlines.append(DescontoNotaVendedorInline)
            
        return inlines

@admin.register(RegraFreteMatriz)
class RegraFreteMatrizAdmin(admin.ModelAdmin):
    list_display = ['tabela', 'ordem', 'peso_inicio', 'peso_fim', 'preco_inicio', 'preco_fim', 'valor_frete']
    list_filter = ['tabela']

@admin.register(TabelaTaxa)
class TabelaTaxaAdmin(admin.ModelAdmin):
    class RegraTaxaInline(admin.TabularInline):
        model = RegraTaxa
        extra = 1
        fields = ['preco_inicio', 'preco_fim', 'valor_taxa', 'ativo']
    
    list_display = ['nome', 'ativo']
    inlines = [RegraTaxaInline]
