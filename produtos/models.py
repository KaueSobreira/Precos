from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal

from canais_vendas.models import CanalVenda


class Produto(models.Model):
    """
    Produto cadastrado no sistema.
    Contém informações básicas, dimensões e pesos.
    O custo é calculado automaticamente a partir da ficha técnica.
    """
    titulo = models.CharField(
        max_length=255,
        verbose_name='Título Principal'
    )
    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='SKU'
    )
    ean = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='EAN'
    )

    # Dimensões (em cm)
    largura = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Largura (cm)'
    )
    altura = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Altura (cm)'
    )
    profundidade = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Profundidade (cm)'
    )

    # Peso físico (digitado pelo usuário, em kg)
    peso_fisico = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name='Peso Físico (kg)'
    )

    # Títulos secundários (armazenados como JSON)
    titulos_secundarios = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Títulos Secundários'
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['titulo']

    def __str__(self):
        return f"{self.sku} - {self.titulo}"

    @property
    def peso_cubico(self):
        """
        Peso cúbico calculado: (L * A * P) / 6000
        Retorna em kg.
        """
        volume = self.largura * self.altura * self.profundidade
        return volume / Decimal('6000')

    @property
    def peso_produto(self):
        """
        Peso do produto para cálculo de frete.
        Retorna o maior entre peso físico e peso cúbico.
        """
        return max(self.peso_fisico, self.peso_cubico)

    @property
    def custo(self):
        """
        Custo total do produto (2 casas decimais).
        Soma dos custos totais de todos os itens da ficha técnica.
        """
        total = Decimal('0.000')
        for item in self.itens_ficha.all():
            total += item.custo_total
        return total.quantize(Decimal('0.01'))

    def calcular_preco_venda(self, canal, frete=None):
        """
        Calcula o preço de venda para um canal específico.
        preco = (markup_frete * frete) + (custo * markup_venda)
        """
        if frete is None:
            frete = canal.obter_frete(peso_produto=self.peso_produto)

        preco_frete = canal.markup_frete * frete
        preco_custo = self.custo * canal.markup_venda
        return (preco_frete + preco_custo).quantize(Decimal('0.01'))

    def calcular_preco_promocao(self, canal, frete=None):
        """
        Calcula o preço promocional para um canal específico.
        preco = (markup_frete * frete) + (custo * markup_promocao)
        """
        if frete is None:
            frete = canal.obter_frete(peso_produto=self.peso_produto)

        preco_frete = canal.markup_frete * frete
        preco_custo = self.custo * canal.markup_promocao
        return (preco_frete + preco_custo).quantize(Decimal('0.01'))

    def calcular_preco_minimo(self, canal, frete=None):
        """
        Calcula o preço mínimo para um canal específico.
        preco = (markup_frete * frete) + (custo * markup_minimo)
        """
        if frete is None:
            frete = canal.obter_frete(peso_produto=self.peso_produto)

        preco_frete = canal.markup_frete * frete
        preco_custo = self.custo * canal.markup_minimo
        return (preco_frete + preco_custo).quantize(Decimal('0.01'))


class ItemFichaTecnica(models.Model):
    """
    Item da ficha técnica (kit) de um produto.
    Cada item tem código, descrição, quantidade, unidade e custo unitário.
    """
    UNIDADE_CHOICES = [
        ('UN', 'Unidade'),
        ('PC', 'Peça'),
        ('CJ', 'Conjunto'),
        ('KG', 'Quilograma'),
        ('G', 'Grama'),
        ('M', 'Metro'),
        ('CM', 'Centímetro'),
        ('M2', 'Metro Quadrado'),
        ('L', 'Litro'),
        ('ML', 'Mililitro'),
        ('CX', 'Caixa'),
        ('PCT', 'Pacote'),
        ('PAR', 'Par'),
        ('JG', 'Jogo'),
    ]

    TIPO_CHOICES = [
        ('MP', 'Matéria Prima'),
        ('TR', 'Terceirizado'),
        ('EM', 'Embalagem'),
    ]

    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='itens_ficha',
        verbose_name='Produto'
    )
    tipo = models.CharField(
        max_length=2,
        choices=TIPO_CHOICES,
        default='MP',
        verbose_name='Tipo de Item'
    )
    codigo = models.CharField(
        max_length=50,
        verbose_name='Código do Item'
    )
    descricao = models.CharField(
        max_length=255,
        verbose_name='Descrição'
    )
    unidade = models.CharField(
        max_length=5,
        choices=UNIDADE_CHOICES,
        default='UN',
        verbose_name='Unidade'
    )
    quantidade = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Quantidade'
    )
    custo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Custo Unitário (R$)'
    )
    multiplicador = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Multiplicador'
    )

    class Meta:
        verbose_name = 'Item da Ficha Técnica'
        verbose_name_plural = 'Itens da Ficha Técnica'
        ordering = ['produto', 'tipo', 'codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"

    @property
    def custo_total(self):
        """Custo total do item = quantidade * custo unitário * multiplicador (3 casas decimais)"""
        return (self.quantidade * self.custo_unitario * self.multiplicador).quantize(Decimal('0.001'))


class PrecoProdutoCanal(models.Model):
    """
    Preço de um produto em um canal de venda específico.
    Armazena os preços calculados e permite sobrescrita manual.
    Qualquer alteração gera um registro no histórico.
    """
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='precos_canais',
        verbose_name='Produto'
    )
    canal = models.ForeignKey(
        CanalVenda,
        on_delete=models.CASCADE,
        related_name='precos_produtos',
        verbose_name='Canal de Venda'
    )

    # Flag para usar valores calculados automaticamente
    usar_calculo_automatico = models.BooleanField(
        default=True,
        verbose_name='Usar Cálculo Automático',
        help_text='Se desmarcado, usa os valores manuais abaixo'
    )

    # Valores manuais (sobrescritos)
    preco_venda_manual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Preço de Venda (Manual)'
    )
    preco_promocao_manual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Preço Promoção (Manual)'
    )
    preco_minimo_manual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Preço Mínimo (Manual)'
    )

    # Frete específico para este produto/canal (opcional)
    frete_especifico = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Frete Específico (R$)',
        help_text='Se preenchido, sobrescreve o frete do canal'
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Preço Produto/Canal'
        verbose_name_plural = 'Preços Produtos/Canais'
        unique_together = [['produto', 'canal']]
        ordering = ['produto', 'canal']

    def __str__(self):
        return f"{self.produto.sku} - {self.canal.nome}"

    @property
    def frete_aplicado(self):
        """Retorna o frete aplicado (específico ou do canal)"""
        if self.frete_especifico is not None:
            return self.frete_especifico
        return self.canal.obter_frete(peso_produto=self.produto.peso_produto)

    @property
    def preco_venda(self):
        """Preço de venda (manual ou calculado)"""
        if not self.usar_calculo_automatico and self.preco_venda_manual is not None:
            return self.preco_venda_manual
        return self.produto.calcular_preco_venda(self.canal, self.frete_aplicado)

    @property
    def preco_promocao(self):
        """Preço promocional (manual ou calculado)"""
        if not self.usar_calculo_automatico and self.preco_promocao_manual is not None:
            return self.preco_promocao_manual
        return self.produto.calcular_preco_promocao(self.canal, self.frete_aplicado)

    @property
    def preco_minimo(self):
        """Preço mínimo (manual ou calculado)"""
        if not self.usar_calculo_automatico and self.preco_minimo_manual is not None:
            return self.preco_minimo_manual
        return self.produto.calcular_preco_minimo(self.canal, self.frete_aplicado)

    @property
    def desconto_maximo_percentual(self):
        """
        Desconto máximo permitido em percentual.
        ((preco_venda - preco_minimo) / preco_venda) * 100
        """
        if self.preco_venda <= 0:
            return Decimal('0.00')
        return (
            (self.preco_venda - self.preco_minimo) / self.preco_venda * Decimal('100')
        ).quantize(Decimal('0.01'))

    def clean(self):
        """Validações do preço"""
        # Se usar valores manuais, validar que promoção >= mínimo
        if not self.usar_calculo_automatico:
            preco_promo = self.preco_promocao_manual or Decimal('0')
            preco_min = self.preco_minimo_manual or Decimal('0')
            if preco_promo < preco_min:
                raise ValidationError(
                    'O preço de promoção não pode ser menor que o preço mínimo'
                )

    def salvar_historico(self, usuario=None, motivo=''):
        """Salva o estado atual no histórico antes de qualquer alteração"""
        HistoricoPreco.objects.create(
            produto=self.produto,
            canal=self.canal,
            grupo=self.canal.grupo,
            # Parâmetros do canal
            imposto=self.canal.imposto_efetivo,
            operacao=self.canal.operacao_efetivo,
            lucro=self.canal.lucro_efetivo,
            promocao_perc=self.canal.promocao_efetivo,
            minimo_perc=self.canal.minimo_efetivo,
            ads=self.canal.ads_efetivo,
            comissao=self.canal.comissao_efetivo,
            # Frete
            frete_aplicado=self.frete_aplicado,
            # Markups
            markup_frete=self.canal.markup_frete,
            markup_venda=self.canal.markup_venda,
            markup_promocao=self.canal.markup_promocao,
            markup_minimo=self.canal.markup_minimo,
            # Preços
            custo=self.produto.custo,
            preco_venda=self.preco_venda,
            preco_promocao=self.preco_promocao,
            preco_minimo=self.preco_minimo,
            # Metadados
            usuario=usuario,
            motivo=motivo
        )

    @transaction.atomic
    def save(self, *args, usuario=None, motivo='', **kwargs):
        """
        Salva o preço.
        Se já existe, salva o histórico antes de atualizar.
        """
        self.full_clean()

        # Se já existe, salvar histórico
        if self.pk:
            self.salvar_historico(usuario=usuario, motivo=motivo)

        super().save(*args, **kwargs)


class HistoricoPreco(models.Model):
    """
    Histórico imutável de preços.
    Cada versão salva todos os parâmetros e valores calculados.
    """
    # Referências
    produto = models.ForeignKey(
        Produto,
        on_delete=models.SET_NULL,
        null=True,
        related_name='historico_precos',
        verbose_name='Produto'
    )
    canal = models.ForeignKey(
        CanalVenda,
        on_delete=models.SET_NULL,
        null=True,
        related_name='historico_precos',
        verbose_name='Canal de Venda'
    )
    grupo = models.ForeignKey(
        'grupo_vendas.GrupoCanais',
        on_delete=models.SET_NULL,
        null=True,
        related_name='historico_precos',
        verbose_name='Grupo'
    )

    # Snapshot dos dados no momento do registro
    sku_produto = models.CharField(
        max_length=50,
        verbose_name='SKU do Produto'
    )
    nome_canal = models.CharField(
        max_length=100,
        verbose_name='Nome do Canal'
    )
    nome_grupo = models.CharField(
        max_length=100,
        verbose_name='Nome do Grupo'
    )

    # Parâmetros (%)
    imposto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Imposto (%)'
    )
    operacao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Operação (%)'
    )
    lucro = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Lucro (%)'
    )
    promocao_perc = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Promoção (%)'
    )
    minimo_perc = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Mínimo (%)'
    )
    ads = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Ads (%)'
    )
    comissao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Comissão (%)'
    )

    # Frete
    frete_aplicado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Frete Aplicado (R$)'
    )

    # Markups
    markup_frete = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        verbose_name='Markup Frete'
    )
    markup_venda = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        verbose_name='Markup Venda'
    )
    markup_promocao = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        verbose_name='Markup Promoção'
    )
    markup_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        verbose_name='Markup Mínimo'
    )

    # Valores
    custo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Custo (R$)'
    )
    preco_venda = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço de Venda (R$)'
    )
    preco_promocao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço Promoção (R$)'
    )
    preco_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço Mínimo (R$)'
    )

    # Auditoria
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historico_precos',
        verbose_name='Usuário'
    )
    motivo = models.TextField(
        blank=True,
        verbose_name='Motivo da Alteração'
    )
    data_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data/Hora do Registro'
    )

    class Meta:
        verbose_name = 'Histórico de Preço'
        verbose_name_plural = 'Histórico de Preços'
        ordering = ['-data_registro']

    def __str__(self):
        return f"{self.sku_produto} - {self.nome_canal} ({self.data_registro.strftime('%d/%m/%Y %H:%M')})"

    def save(self, *args, **kwargs):
        # Preencher snapshots dos nomes
        if self.produto:
            self.sku_produto = self.produto.sku
        if self.canal:
            self.nome_canal = self.canal.nome
        if self.grupo:
            self.nome_grupo = self.grupo.nome

        # Histórico é imutável - não permite update
        if self.pk:
            raise ValidationError('Registros de histórico não podem ser alterados')

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Registros de histórico não podem ser excluídos')
