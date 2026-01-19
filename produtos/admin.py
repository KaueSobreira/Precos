from django.contrib import admin
from .models import Produto, ItemFichaTecnica, PrecoProdutoCanal, HistoricoPreco


class ItemFichaTecnicaInline(admin.TabularInline):
    model = ItemFichaTecnica
    extra = 1


class PrecoProdutoCanalInline(admin.TabularInline):
    model = PrecoProdutoCanal
    extra = 0
    readonly_fields = ['preco_venda_calc', 'preco_promocao_calc', 'preco_minimo_calc', 'desconto_max']
    fields = [
        'canal', 'ativo', 'usar_calculo_automatico',
        'frete_especifico', 'preco_venda_calc', 'preco_promocao_calc',
        'preco_minimo_calc', 'desconto_max'
    ]

    def preco_venda_calc(self, obj):
        if obj.pk:
            return f"R$ {obj.preco_venda:,.2f}"
        return "-"
    preco_venda_calc.short_description = "Preço Venda"

    def preco_promocao_calc(self, obj):
        if obj.pk:
            return f"R$ {obj.preco_promocao:,.2f}"
        return "-"
    preco_promocao_calc.short_description = "Preço Promoção"

    def preco_minimo_calc(self, obj):
        if obj.pk:
            return f"R$ {obj.preco_minimo:,.2f}"
        return "-"
    preco_minimo_calc.short_description = "Preço Mínimo"

    def desconto_max(self, obj):
        if obj.pk:
            return f"{obj.desconto_maximo_percentual}%"
        return "-"
    desconto_max.short_description = "Desc. Máx."


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = [
        'sku', 'titulo', 'peso_fisico', 'peso_cubico_display',
        'peso_produto_display', 'custo_display', 'ativo'
    ]
    list_filter = ['ativo']
    search_fields = ['sku', 'titulo', 'ean']
    readonly_fields = [
        'criado_em', 'atualizado_em',
        'peso_cubico_display', 'peso_produto_display', 'custo_display'
    ]
    inlines = [ItemFichaTecnicaInline, PrecoProdutoCanalInline]

    fieldsets = [
        ('Informações Básicas', {
            'fields': ['titulo', 'sku', 'ean', 'ativo']
        }),
        ('Dimensões (cm)', {
            'fields': [('largura', 'altura', 'profundidade')]
        }),
        ('Peso', {
            'fields': [
                'peso_fisico',
                ('peso_cubico_display', 'peso_produto_display')
            ]
        }),
        ('Custo', {
            'fields': ['custo_display'],
            'description': 'O custo é calculado automaticamente a partir da ficha técnica.'
        }),
        ('Títulos Secundários', {
            'fields': ['titulos_secundarios'],
            'classes': ['collapse']
        }),
        ('Metadados', {
            'fields': ['criado_em', 'atualizado_em'],
            'classes': ['collapse']
        }),
    ]

    def peso_cubico_display(self, obj):
        return f"{obj.peso_cubico:.3f} kg"
    peso_cubico_display.short_description = "Peso Cúbico"

    def peso_produto_display(self, obj):
        return f"{obj.peso_produto:.3f} kg"
    peso_produto_display.short_description = "Peso Produto (Frete)"

    def custo_display(self, obj):
        return f"R$ {obj.custo:,.2f}"
    custo_display.short_description = "Custo Total"


@admin.register(ItemFichaTecnica)
class ItemFichaTecnicaAdmin(admin.ModelAdmin):
    list_display = ['produto', 'codigo', 'descricao', 'quantidade', 'custo_unitario', 'custo_total_display']
    list_filter = ['produto']
    search_fields = ['codigo', 'descricao', 'produto__sku']

    def custo_total_display(self, obj):
        return f"R$ {obj.custo_total:,.2f}"
    custo_total_display.short_description = "Custo Total"


@admin.register(PrecoProdutoCanal)
class PrecoProdutoCanalAdmin(admin.ModelAdmin):
    list_display = [
        'produto', 'canal', 'usar_calculo_automatico',
        'preco_venda_display', 'preco_promocao_display',
        'preco_minimo_display', 'desconto_max_display', 'ativo'
    ]
    list_filter = ['canal__grupo', 'canal', 'usar_calculo_automatico', 'ativo']
    search_fields = ['produto__sku', 'produto__titulo', 'canal__nome']
    readonly_fields = [
        'criado_em', 'atualizado_em',
        'preco_venda_display', 'preco_promocao_display',
        'preco_minimo_display', 'desconto_max_display', 'frete_aplicado_display'
    ]
    autocomplete_fields = ['produto', 'canal']

    fieldsets = [
        ('Produto/Canal', {
            'fields': ['produto', 'canal', 'ativo']
        }),
        ('Configuração', {
            'fields': ['usar_calculo_automatico', 'frete_especifico']
        }),
        ('Valores Manuais', {
            'fields': [
                'preco_venda_manual',
                'preco_promocao_manual',
                'preco_minimo_manual'
            ],
            'description': 'Só são usados se "Usar Cálculo Automático" estiver desmarcado.'
        }),
        ('Valores Calculados (Somente Leitura)', {
            'fields': [
                'frete_aplicado_display',
                ('preco_venda_display', 'preco_promocao_display'),
                ('preco_minimo_display', 'desconto_max_display')
            ]
        }),
        ('Metadados', {
            'fields': ['criado_em', 'atualizado_em'],
            'classes': ['collapse']
        }),
    ]

    def preco_venda_display(self, obj):
        return f"R$ {obj.preco_venda:,.2f}"
    preco_venda_display.short_description = "Preço Venda"

    def preco_promocao_display(self, obj):
        return f"R$ {obj.preco_promocao:,.2f}"
    preco_promocao_display.short_description = "Preço Promoção"

    def preco_minimo_display(self, obj):
        return f"R$ {obj.preco_minimo:,.2f}"
    preco_minimo_display.short_description = "Preço Mínimo"

    def desconto_max_display(self, obj):
        return f"{obj.desconto_maximo_percentual}%"
    desconto_max_display.short_description = "Desconto Máximo"

    def frete_aplicado_display(self, obj):
        return f"R$ {obj.frete_aplicado:,.2f}"
    frete_aplicado_display.short_description = "Frete Aplicado"


@admin.register(HistoricoPreco)
class HistoricoPrecoAdmin(admin.ModelAdmin):
    list_display = [
        'data_registro', 'sku_produto', 'nome_canal', 'nome_grupo',
        'preco_venda', 'preco_promocao', 'preco_minimo', 'usuario'
    ]
    list_filter = ['nome_grupo', 'nome_canal', 'data_registro']
    search_fields = ['sku_produto', 'nome_canal']
    readonly_fields = [
        'produto', 'canal', 'grupo',
        'sku_produto', 'nome_canal', 'nome_grupo',
        'imposto', 'operacao', 'lucro', 'promocao_perc',
        'minimo_perc', 'ads', 'comissao',
        'frete_aplicado',
        'markup_frete', 'markup_venda', 'markup_promocao', 'markup_minimo',
        'custo', 'preco_venda', 'preco_promocao', 'preco_minimo',
        'usuario', 'motivo', 'data_registro'
    ]
    date_hierarchy = 'data_registro'
    ordering = ['-data_registro']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
