from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import transaction
from decimal import Decimal

from canais_vendas.models import CanalVenda

class Produto(models.Model):
    titulo = models.CharField(max_length=255, verbose_name='Título Principal')
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    ean = models.CharField(max_length=20, blank=True, verbose_name='EAN')
    largura = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    altura = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    profundidade = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    peso_fisico = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])
    titulos_secundarios = models.JSONField(default=list, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sku} - {self.titulo}"

    @property
    def peso_cubico(self):
        return (self.largura * self.altura * self.profundidade) / Decimal('6000')

    @property
    def peso_produto(self):
        return max(self.peso_fisico, self.peso_cubico)

    @property
    def custo(self):
        total = Decimal('0.000')
        for item in self.itens_ficha.all():
            total += item.custo_total
        return total.quantize(Decimal('0.01'))

    def _calcular_preco_iterativo(self, canal, markup_target, frete_fixo=None, max_iteracoes=10):
        # Resolve: Preço = (Custo + Taxa(Preço)) * Markup + Frete(Peso, Preço) * Markup_Frete
        peso = self.peso_produto
        custo = self.custo
        
        preco_venda = Decimal('0.00')
        frete = frete_fixo if frete_fixo is not None else canal.obter_frete(peso_produto=peso)
        taxa = Decimal('0.00')

        for _ in range(max_iteracoes):
            # 1. Calcula novo preço baseado nos componentes atuais
            # Nota: Taxa e Frete podem depender do preço
            novo_preco = ((custo + taxa) * markup_target) + (frete * canal.markup_frete)
            novo_preco = novo_preco.quantize(Decimal('0.01'))

            # 2. Atualiza componentes baseados no novo preço
            nova_taxa = canal.obter_taxa_extra(preco_venda=novo_preco)
            novo_frete = frete_fixo if frete_fixo is not None else canal.obter_frete(peso_produto=peso, preco_venda=novo_preco)

            if novo_preco == preco_venda and nova_taxa == taxa and novo_frete == frete:
                break
            
            preco_venda = novo_preco
            taxa = nova_taxa
            frete = novo_frete

        return preco_venda

    def calcular_preco_venda(self, canal, frete=None):
        return self._calcular_preco_iterativo(canal, canal.markup_venda, frete_fixo=frete)

    def calcular_preco_promocao(self, canal, frete=None):
        return self._calcular_preco_iterativo(canal, canal.markup_promocao, frete_fixo=frete)

    def calcular_preco_minimo(self, canal, frete=None):
        return self._calcular_preco_iterativo(canal, canal.markup_minimo, frete_fixo=frete)

class ItemFichaTecnica(models.Model):
    UNIDADE_CHOICES = [
        ('UN', 'Unidade'), ('PC', 'Peça'), ('CJ', 'Conjunto'),
        ('KG', 'Quilograma'), ('G', 'Grama'), ('M', 'Metro'),
        ('CM', 'Centímetro'), ('M2', 'Metro Quadrado'), ('L', 'Litro'),
        ('ML', 'Mililitro'), ('CX', 'Caixa'), ('PCT', 'Pacote'),
        ('PAR', 'Par'), ('JG', 'Jogo'),
    ]
    TIPO_CHOICES = [
        ('MP', 'Matéria Prima'), ('TR', 'Terceirizado'), ('EM', 'Embalagem'),
    ]

    produto = models.ForeignKey(Produto, related_name='itens_ficha', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=2, choices=TIPO_CHOICES, default='MP')
    codigo = models.CharField(max_length=50)
    descricao = models.CharField(max_length=255)
    unidade = models.CharField(max_length=5, choices=UNIDADE_CHOICES, default='UN')
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=3)
    multiplicador = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.00'))

    @property
    def custo_total(self):
        return (self.quantidade * self.custo_unitario * self.multiplicador).quantize(Decimal('0.001'))

class PrecoProdutoCanal(models.Model):
    produto = models.ForeignKey(Produto, related_name='precos_canais', on_delete=models.CASCADE)
    canal = models.ForeignKey(CanalVenda, related_name='precos_produtos', on_delete=models.CASCADE)
    usar_calculo_automatico = models.BooleanField(default=True)
    
    preco_venda_manual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_promocao_manual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_minimo_manual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    frete_especifico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    @property
    def frete_aplicado(self):
        if self.frete_especifico is not None: return self.frete_especifico
        # Preço de venda calculado para obter o frete correto da matriz
        # Nota: Idealmente o frete depende do preço que está sendo calculado (venda/promo/min), 
        # mas para exibição geral usamos o de venda como base.
        return self.canal.obter_frete(peso_produto=self.produto.peso_produto, preco_venda=self.preco_venda)

    @property
    def preco_venda(self):
        if not self.usar_calculo_automatico and self.preco_venda_manual: return self.preco_venda_manual
        return self.produto.calcular_preco_venda(self.canal, self.frete_especifico)

    @property
    def preco_promocao(self):
        if not self.usar_calculo_automatico and self.preco_promocao_manual: return self.preco_promocao_manual
        return self.produto.calcular_preco_promocao(self.canal, self.frete_especifico)

    @property
    def preco_minimo(self):
        if not self.usar_calculo_automatico and self.preco_minimo_manual: return self.preco_minimo_manual
        return self.produto.calcular_preco_minimo(self.canal, self.frete_especifico)

    @property
    def desconto_maximo_percentual(self):
        if self.preco_venda <= 0: return Decimal('0.00')
        return ((self.preco_venda - self.preco_minimo) / self.preco_venda * Decimal('100')).quantize(Decimal('0.01'))

    def salvar_historico(self, usuario=None, motivo=''):
        HistoricoPreco.objects.create(
            produto=self.produto, canal=self.canal,
            custo=self.produto.custo,
            preco_venda=self.preco_venda,
            preco_promocao=self.preco_promocao,
            preco_minimo=self.preco_minimo,
            frete_aplicado=self.frete_aplicado,
            taxa_extra=self.canal.obter_taxa_extra(self.preco_venda),
            usuario=usuario, motivo=motivo
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.pk: self.salvar_historico()
        super().save(*args, **kwargs)

class HistoricoPreco(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True)
    canal = models.ForeignKey(CanalVenda, on_delete=models.SET_NULL, null=True)
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    preco_promocao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_minimo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    frete_aplicado = models.DecimalField(max_digits=10, decimal_places=2)
    taxa_extra = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    data_registro = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    motivo = models.TextField(blank=True)