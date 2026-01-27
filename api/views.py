from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from django.db import transaction
from drf_spectacular.utils import extend_schema

from produtos.models import Produto, TituloProduto, ItemFichaTecnica, PrecoProdutoCanal
from canais_vendas.models import CanalVenda
from .serializers import ProdutoCreateSerializer, ProdutoListSerializer


class ProdutoPagination(CursorPagination):
    page_size = 50
    ordering = '-criado_em'


class ProdutoViewSet(viewsets.ViewSet):
    pagination_class = ProdutoPagination

    @extend_schema(
        responses=ProdutoListSerializer(many=True),
        description='Lista todos os produtos com preços por canal.',
    )
    def list(self, request):
        queryset = Produto.objects.prefetch_related(
            'titulos',
            'itens_ficha',
            'precos_canais__canal__grupo',
        ).order_by('-criado_em')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ProdutoListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=ProdutoCreateSerializer,
        responses={201: ProdutoListSerializer},
        description='Cria um produto completo com títulos, ficha técnica e preços por canal.',
    )
    @transaction.atomic
    def create(self, request):
        serializer = ProdutoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 1. Criar produto
        produto = Produto.objects.create(
            titulo=data['titulo'],
            sku=data['sku'],
            ean=data.get('ean', ''),
            mlb=data.get('mlb', ''),
            mlb_vinculado=data.get('mlb_vinculado', ''),
            desconto_estrategico=data.get('desconto_estrategico', False),
            largura=data['largura'],
            altura=data['altura'],
            profundidade=data['profundidade'],
            peso_fisico=data['peso_fisico'],
        )

        # 2. Criar títulos secundários
        for titulo_data in data.get('titulos_secundarios', []):
            TituloProduto.objects.create(
                produto=produto,
                titulo=titulo_data['titulo'],
            )

        # 3. Criar itens da ficha técnica
        for item_data in data.get('ficha_tecnica', []):
            ItemFichaTecnica.objects.create(
                produto=produto,
                tipo=item_data['tipo'],
                codigo=item_data['codigo'],
                descricao=item_data['descricao'],
                unidade=item_data.get('unidade', 'UN'),
                quantidade=item_data['quantidade'],
                custo_unitario=item_data['custo_unitario'],
                multiplicador=item_data.get('multiplicador', 1),
            )

        # 4. Criar preços por canal
        errors = []
        for i, preco_data in enumerate(data.get('precos_canais', [])):
            canal = self._resolver_canal(preco_data, i, errors)
            if canal is None:
                continue

            PrecoProdutoCanal.objects.create(
                produto=produto,
                canal=canal,
                usar_calculo_automatico=preco_data.get('usar_calculo_automatico', True),
                imposto=preco_data.get('imposto'),
                operacao=preco_data.get('operacao'),
                lucro=preco_data.get('lucro'),
                promocao=preco_data.get('promocao'),
                minimo=preco_data.get('minimo'),
                ads=preco_data.get('ads'),
                comissao=preco_data.get('comissao'),
                preco_venda_manual=preco_data.get('preco_venda_manual'),
                preco_promocao_manual=preco_data.get('preco_promocao_manual'),
                preco_minimo_manual=preco_data.get('preco_minimo_manual'),
                frete_especifico=preco_data.get('frete_especifico'),
            )

        # Recarregar produto com todos os relacionamentos
        produto.refresh_from_db()
        output = ProdutoListSerializer(produto).data

        if errors:
            output['avisos'] = errors

        return Response(output, status=status.HTTP_201_CREATED)

    def _resolver_canal(self, preco_data, index, errors):
        canal_id = preco_data.get('canal_id')
        if canal_id:
            try:
                return CanalVenda.objects.get(pk=canal_id, ativo=True)
            except CanalVenda.DoesNotExist:
                errors.append(f'precos_canais[{index}]: canal_id={canal_id} não encontrado.')
                return None

        canal_nome = preco_data.get('canal_nome', '')
        grupo_nome = preco_data.get('grupo_nome', '')
        try:
            return CanalVenda.objects.get(nome=canal_nome, grupo__nome=grupo_nome, ativo=True)
        except CanalVenda.DoesNotExist:
            errors.append(
                f'precos_canais[{index}]: canal "{canal_nome}" no grupo "{grupo_nome}" não encontrado.'
            )
            return None
        except CanalVenda.MultipleObjectsReturned:
            errors.append(
                f'precos_canais[{index}]: múltiplos canais "{canal_nome}" no grupo "{grupo_nome}". Use canal_id.'
            )
            return None
