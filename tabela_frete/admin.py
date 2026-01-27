from django.contrib import admin
from .models import TabelaFrete, RegraFreteMatriz, RegraFreteSimples, RegraFreteEspecial, DescontoNotaVendedor, TabelaTaxa, RegraTaxa


class RegraFreteMatrizPrecoInline(admin.TabularInline):
    """Inline para tabelas tipo 'matriz' (Peso x Preco)"""
    model = RegraFreteMatriz
    extra = 1
    fields = ['ordem', 'peso_inicio', 'peso_fim', 'preco_inicio', 'preco_fim', 'valor_frete', 'excedente', 'ativo']
    ordering = ['ordem', 'peso_inicio', 'preco_inicio']
    verbose_name = "Regra Matriz (Peso x Preco)"
    verbose_name_plural = "Regras Matriz (Peso x Preco)"


class RegraFreteMatrizScoreInline(admin.TabularInline):
    """Inline para tabelas tipo 'matriz_score' (Peso x Score)"""
    model = RegraFreteMatriz
    extra = 1
    fields = ['ordem', 'peso_inicio', 'peso_fim', 'score_inicio', 'score_fim', 'valor_frete', 'excedente', 'ativo']
    ordering = ['ordem', 'peso_inicio', 'score_inicio']
    verbose_name = "Regra Matriz (Peso x Score)"
    verbose_name_plural = "Regras Matriz (Peso x Score)"


class RegraFreteSimplesInline(admin.TabularInline):
    model = RegraFreteSimples
    extra = 1
    fields = ['inicio', 'fim', 'valor_frete', 'excedente', 'ativo']
    ordering = ['inicio']
    verbose_name = "Regra Simples (Peso ou Preco)"
    verbose_name_plural = "Regras Simples (Peso ou Preco)"


class RegraFreteEspecialInline(admin.TabularInline):
    model = RegraFreteEspecial
    extra = 1
    fields = ['ordem', 'largura_min', 'altura_min', 'profundidade_min', 'peso_min', 'valor_frete', 'ativo']
    ordering = ['ordem']
    verbose_name = "Regra Especial"
    verbose_name_plural = "Regras Especiais (Prioridade)"


class DescontoNotaVendedorInline(admin.TabularInline):
    model = DescontoNotaVendedor
    extra = 1


@admin.register(TabelaFrete)
class TabelaFreteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'ativo', 'atualizado_em']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome']

    fieldsets = [
        ('Informacoes Basicas', {
            'fields': ['nome', 'tipo', 'descricao', 'ativo']
        }),
        ('Taxa Fixa Adicional', {
            'fields': ['adicionar_taxa_fixa', 'valor_taxa_fixa'],
            'description': 'Valor fixo adicionado ao frete APOS o calculo de descontos.'
        }),
        ('Excedente (>1m)', {
            'fields': ['usa_tabela_excedente'],
            'description': 'Habilita regras diferenciadas para produtos com dimensao superior a 1 metro.'
        }),
        ('Frete baseado em Preco Promocional', {
            'fields': ['usar_preco_promocao'],
            'description': 'Se marcado, o frete sera calculado com base no preco promocional em vez do preco de venda.'
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
                inlines.append(RegraFreteMatrizPrecoInline)
            elif obj.tipo == 'matriz_score':
                inlines.append(RegraFreteMatrizScoreInline)
            elif obj.tipo in ['peso', 'preco']:
                inlines.append(RegraFreteSimplesInline)

        # Regras especiais sempre visiveis (todas as tabelas suportam)
        inlines.append(RegraFreteEspecialInline)

        # Descontos por nota
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
