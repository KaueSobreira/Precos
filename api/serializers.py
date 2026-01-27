from rest_framework import serializers
from decimal import Decimal

from produtos.models import Produto, TituloProduto, ItemFichaTecnica, PrecoProdutoCanal
from canais_vendas.models import CanalVenda


# ============================================================
# Serializers de escrita (POST)
# ============================================================

class TituloSecundarioCreateSerializer(serializers.Serializer):
    titulo = serializers.CharField(max_length=255)


class FichaTecnicaItemCreateSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=ItemFichaTecnica.TIPO_CHOICES)
    codigo = serializers.CharField(max_length=50)
    descricao = serializers.CharField(max_length=255)
    unidade = serializers.ChoiceField(choices=ItemFichaTecnica.UNIDADE_CHOICES, default='UN')
    quantidade = serializers.DecimalField(max_digits=10, decimal_places=2)
    custo_unitario = serializers.DecimalField(max_digits=10, decimal_places=3)
    multiplicador = serializers.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.00'))


class PrecoCanalCreateSerializer(serializers.Serializer):
    canal_id = serializers.IntegerField(required=False)
    canal_nome = serializers.CharField(max_length=100, required=False)
    grupo_nome = serializers.CharField(max_length=100, required=False)

    # Overrides de parâmetros
    imposto = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    operacao = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    lucro = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    promocao = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    minimo = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    ads = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    comissao = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)

    usar_calculo_automatico = serializers.BooleanField(default=True)
    preco_venda_manual = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    preco_promocao_manual = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    preco_minimo_manual = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    frete_especifico = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    def validate(self, data):
        has_id = 'canal_id' in data and data['canal_id'] is not None
        has_nome = 'canal_nome' in data and data['canal_nome']
        if not has_id and not has_nome:
            raise serializers.ValidationError(
                'Informe canal_id ou (canal_nome + grupo_nome) para identificar o canal.'
            )
        return data


class ProdutoCreateSerializer(serializers.Serializer):
    titulo = serializers.CharField(max_length=255)
    mlb = serializers.CharField(max_length=50, required=False, default='')
    mlb_vinculado = serializers.CharField(max_length=50, required=False, default='')
    sku = serializers.CharField(max_length=50)
    ean = serializers.CharField(max_length=20, required=False, default='')
    largura = serializers.DecimalField(max_digits=10, decimal_places=2)
    altura = serializers.DecimalField(max_digits=10, decimal_places=2)
    profundidade = serializers.DecimalField(max_digits=10, decimal_places=2)
    peso_fisico = serializers.DecimalField(max_digits=10, decimal_places=3)
    desconto_estrategico = serializers.BooleanField(default=False)

    titulos_secundarios = TituloSecundarioCreateSerializer(many=True, required=False, default=[])
    ficha_tecnica = FichaTecnicaItemCreateSerializer(many=True, required=False, default=[])
    precos_canais = PrecoCanalCreateSerializer(many=True, required=False, default=[])

    def validate_sku(self, value):
        if Produto.objects.filter(sku=value).exists():
            raise serializers.ValidationError(f'Já existe um produto com SKU "{value}".')
        return value


# ============================================================
# Serializers de leitura (GET)
# ============================================================

class TituloSecundarioReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TituloProduto
        fields = ['id', 'titulo', 'ativo']


class FichaTecnicaItemReadSerializer(serializers.ModelSerializer):
    custo_total = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)

    class Meta:
        model = ItemFichaTecnica
        fields = ['id', 'tipo', 'codigo', 'descricao', 'unidade', 'quantidade', 'custo_unitario', 'multiplicador', 'custo_total']


class PrecoProdutoCanalReadSerializer(serializers.ModelSerializer):
    canal_nome = serializers.CharField(source='canal.nome', read_only=True)
    grupo_nome = serializers.SerializerMethodField()

    imposto_efetivo = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    operacao_efetivo = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    lucro_efetivo = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    promocao_efetivo = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    minimo_efetivo = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    ads_efetivo = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    comissao_efetivo = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    preco_venda = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    preco_promocao = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    preco_promocao_arredondado = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    preco_minimo = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    preco_minimo_arredondado = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    frete_aplicado = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    custo = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = PrecoProdutoCanal
        fields = [
            'id', 'canal', 'canal_nome', 'grupo_nome',
            'usar_calculo_automatico', 'ativo',
            'imposto', 'operacao', 'lucro', 'promocao', 'minimo', 'ads', 'comissao',
            'imposto_efetivo', 'operacao_efetivo', 'lucro_efetivo',
            'promocao_efetivo', 'minimo_efetivo', 'ads_efetivo', 'comissao_efetivo',
            'preco_venda', 'preco_promocao', 'preco_promocao_arredondado',
            'preco_minimo', 'preco_minimo_arredondado',
            'frete_aplicado', 'frete_especifico', 'custo',
        ]

    def get_grupo_nome(self, obj):
        return obj.canal.grupo.nome if obj.canal.grupo else ''


class ProdutoListSerializer(serializers.ModelSerializer):
    custo = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    peso_cubico = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)
    peso_produto = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)
    titulos_secundarios = TituloSecundarioReadSerializer(source='titulos', many=True, read_only=True)
    ficha_tecnica = FichaTecnicaItemReadSerializer(source='itens_ficha', many=True, read_only=True)
    precos_canais = PrecoProdutoCanalReadSerializer(many=True, read_only=True)

    class Meta:
        model = Produto
        fields = [
            'id', 'titulo', 'mlb', 'mlb_vinculado', 'sku', 'ean',
            'largura', 'altura', 'profundidade',
            'peso_fisico', 'peso_cubico', 'peso_produto',
            'custo', 'desconto_estrategico', 'ativo',
            'titulos_secundarios', 'ficha_tecnica', 'precos_canais',
        ]
