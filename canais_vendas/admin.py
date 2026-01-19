from django.contrib import admin
from .models import TabelaFrete, RegraFrete, CanalVenda


class RegraFreteInline(admin.TabularInline):
    model = RegraFrete
    extra = 1
    ordering = ['ordem']


@admin.register(TabelaFrete)
class TabelaFreteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'ativo', 'atualizado_em']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em']
    inlines = [RegraFreteInline]

    fieldsets = [
        ('Informações Básicas', {
            'fields': ['nome', 'tipo', 'descricao', 'ativo']
        }),
        ('Metadados', {
            'fields': ['criado_em', 'atualizado_em'],
            'classes': ['collapse']
        }),
    ]


@admin.register(RegraFrete)
class RegraFreteAdmin(admin.ModelAdmin):
    list_display = ['tabela', 'ordem', 'tipo_condicao', 'operador', 'valor_limite', 'valor_frete', 'ativo']
    list_filter = ['tabela', 'tipo_condicao', 'ativo']
    ordering = ['tabela', 'ordem']


@admin.register(CanalVenda)
class CanalVendaAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'grupo', 'herdar_grupo', 'tipo_frete',
        'ativo', 'atualizado_em'
    ]
    list_filter = ['grupo', 'herdar_grupo', 'tipo_frete', 'ativo']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em', 'markup_frete', 'markup_venda', 'markup_promocao', 'markup_minimo']
    autocomplete_fields = ['grupo', 'tabela_frete']

    fieldsets = [
        ('Informações Básicas', {
            'fields': ['nome', 'grupo', 'descricao', 'ativo']
        }),
        ('Herança de Parâmetros', {
            'fields': ['herdar_grupo'],
            'description': 'Se marcado, usa os percentuais do grupo. Desmarque para usar valores próprios.'
        }),
        ('Parâmetros do Canal (%)', {
            'fields': [
                ('imposto', 'operacao'),
                ('lucro', 'promocao'),
                ('minimo', 'ads'),
                'comissao'
            ],
            'description': 'Só são usados se "Herdar do grupo" estiver desmarcado.'
        }),
        ('Configuração de Frete', {
            'fields': [
                'tipo_frete',
                ('frete_fixo', 'tabela_frete')
            ]
        }),
        ('Markups Calculados (Somente Leitura)', {
            'fields': [
                ('markup_frete', 'markup_venda'),
                ('markup_promocao', 'markup_minimo')
            ],
            'classes': ['collapse']
        }),
        ('Metadados', {
            'fields': ['criado_em', 'atualizado_em'],
            'classes': ['collapse']
        }),
    ]
