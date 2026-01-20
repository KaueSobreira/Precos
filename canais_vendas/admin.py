from django.contrib import admin
from .models import CanalVenda

@admin.register(CanalVenda)
class CanalVendaAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'grupo', 'herdar_grupo', 'tipo_frete', 'nota_vendedor',
        'ativo', 'atualizado_em'
    ]
    list_filter = ['grupo', 'herdar_grupo', 'tipo_frete', 'nota_vendedor', 'ativo']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em', 'markup_frete', 'markup_venda', 'markup_promocao', 'markup_minimo']
    # autocomplete_fields = ['grupo', 'tabela_frete', 'tabela_taxa'] # Comentar se não estiverem registrados com search_fields na outra app ainda, mas é boa pratica

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
                ('frete_fixo', 'tabela_frete'),
                'nota_vendedor'
            ],
            'description': 'A nota do vendedor é usada para calcular descontos de frete em tabelas que suportam essa funcionalidade.'
        }),
        ('Taxas Extras (Taxa de Venda)', {
            'fields': ['tabela_taxa'],
            'description': 'Configure tabelas de taxas extras (ex: valor fixo por faixa de preço).'
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