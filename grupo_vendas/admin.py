from django.contrib import admin
from .models import GrupoCanais


@admin.register(GrupoCanais)
class GrupoCanaisAdmin(admin.ModelAdmin):
    list_display = [
        'nome', 'is_default', 'imposto', 'operacao', 'lucro',
        'promocao', 'minimo', 'ads', 'comissao', 'atualizado_em'
    ]
    list_filter = ['is_default']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em']

    fieldsets = [
        ('Informações Básicas', {
            'fields': ['nome', 'descricao', 'is_default']
        }),
        ('Parâmetros Padrão (%)', {
            'fields': [
                ('imposto', 'operacao'),
                ('lucro', 'promocao'),
                ('minimo', 'ads'),
                'comissao'
            ]
        }),
        ('Metadados', {
            'fields': ['criado_em', 'atualizado_em'],
            'classes': ['collapse']
        }),
    ]

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_default:
            return False
        return super().has_delete_permission(request, obj)
