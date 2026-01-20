from django.contrib import admin
from .models import Produto, ItemFichaTecnica, PrecoProdutoCanal, HistoricoPreco

class ItemFichaTecnicaInline(admin.TabularInline):
    model = ItemFichaTecnica
    extra = 1

class PrecoProdutoCanalInline(admin.TabularInline):
    model = PrecoProdutoCanal
    extra = 0
    readonly_fields = ['preco_venda_display']
    fields = ['canal', 'ativo', 'usar_calculo_automatico', 'preco_venda_manual', 'frete_especifico', 'preco_venda_display']

    def preco_venda_display(self, obj):
        if obj.pk: return f"R$ {obj.preco_venda:,.2f}"
        return "-"

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['sku', 'titulo', 'custo', 'ativo']
    search_fields = ['sku', 'titulo']
    inlines = [ItemFichaTecnicaInline, PrecoProdutoCanalInline]

@admin.register(PrecoProdutoCanal)
class PrecoProdutoCanalAdmin(admin.ModelAdmin):
    list_display = ['produto', 'canal', 'preco_venda', 'ativo']
    list_filter = ['canal', 'ativo']
    search_fields = ['produto__sku', 'canal__nome']

@admin.register(HistoricoPreco)
class HistoricoPrecoAdmin(admin.ModelAdmin):
    list_display = ['data_registro', 'produto', 'canal', 'preco_venda']
    readonly_fields = ['data_registro', 'produto', 'canal', 'custo', 'preco_venda', 'frete_aplicado', 'taxa_extra', 'usuario', 'motivo']