from django.contrib import admin
from .models import Produto, TituloProduto, ItemFichaTecnica, PrecoProdutoCanal, HistoricoPreco


class TituloProdutoInline(admin.TabularInline):
    model = TituloProduto
    extra = 1
    fields = ['sku', 'titulo', 'ean', 'ativo']


class ItemFichaTecnicaInline(admin.TabularInline):
    model = ItemFichaTecnica
    extra = 1


class PrecoProdutoCanalInline(admin.TabularInline):
    model = PrecoProdutoCanal
    extra = 0
    readonly_fields = ['preco_venda_display']
    fields = ['canal', 'ativo', 'usar_calculo_automatico', 'preco_venda_manual', 'frete_especifico', 'preco_venda_display']

    def preco_venda_display(self, obj):
        if obj.pk:
            return f"R$ {obj.preco_venda:,.2f}"
        return "-"


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['sku', 'titulo', 'custo', 'qtd_titulos', 'ativo']
    search_fields = ['sku', 'titulo', 'titulos__sku', 'titulos__titulo']
    list_filter = ['ativo']
    inlines = [TituloProdutoInline, ItemFichaTecnicaInline, PrecoProdutoCanalInline]

    def qtd_titulos(self, obj):
        return obj.titulos.filter(ativo=True).count()
    qtd_titulos.short_description = 'Títulos'


@admin.register(TituloProduto)
class TituloProdutoAdmin(admin.ModelAdmin):
    list_display = ['sku', 'titulo', 'produto_pai_sku', 'custo', 'ativo']
    list_filter = ['ativo', 'produto']
    search_fields = ['sku', 'titulo', 'produto__sku', 'produto__titulo']
    raw_id_fields = ['produto']
    readonly_fields = ['produto_pai_sku', 'titulo_pai', 'custo', 'peso_produto', 'dimensoes']

    fieldsets = (
        ('Identificação', {
            'fields': ('produto', 'sku', 'titulo', 'ean', 'ativo')
        }),
        ('Dados Herdados do Produto Pai (somente leitura)', {
            'fields': ('produto_pai_sku', 'titulo_pai', 'custo', 'peso_produto', 'dimensoes'),
            'classes': ('collapse',)
        }),
    )

    def produto_pai_sku(self, obj):
        return obj.produto.sku
    produto_pai_sku.short_description = 'SKU do Pai'

    def titulo_pai(self, obj):
        return obj.produto.titulo
    titulo_pai.short_description = 'Título do Pai'

    def custo(self, obj):
        return f"R$ {obj.custo:,.2f}"
    custo.short_description = 'Custo'

    def peso_produto(self, obj):
        return f"{obj.peso_produto:.3f} kg"
    peso_produto.short_description = 'Peso'

    def dimensoes(self, obj):
        return f"{obj.largura} x {obj.altura} x {obj.profundidade} cm"
    dimensoes.short_description = 'Dimensões (L x A x P)'

@admin.register(PrecoProdutoCanal)
class PrecoProdutoCanalAdmin(admin.ModelAdmin):
    list_display = ['produto', 'canal', 'preco_venda', 'ativo']
    list_filter = ['canal', 'ativo']
    search_fields = ['produto__sku', 'canal__nome']

@admin.register(HistoricoPreco)
class HistoricoPrecoAdmin(admin.ModelAdmin):
    list_display = ['data_registro', 'produto', 'canal', 'preco_venda']
    readonly_fields = ['data_registro', 'produto', 'canal', 'custo', 'preco_venda', 'frete_aplicado', 'taxa_extra', 'usuario', 'motivo']