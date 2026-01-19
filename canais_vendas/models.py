from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

from grupo_vendas.models import GrupoCanais


class TabelaFrete(models.Model):
    """
    Tabela de frete reutilizável.
    Pode ser por peso (usa Peso Produto) ou por preço (usa Preço de Venda).
    """
    TIPO_CHOICES = [
        ('peso', 'Por Peso (kg)'),
        ('preco', 'Por Preço (R$)'),
    ]

    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome da Tabela'
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default='peso',
        verbose_name='Tipo de Condição'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Tabela de Frete'
        verbose_name_plural = 'Tabelas de Frete'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"

    def calcular_frete(self, valor):
        """
        Calcula o frete baseado no valor (peso ou preço).
        Retorna o valor do frete aplicável.
        """
        regras = self.regras.filter(ativo=True).order_by('ordem')

        for regra in regras:
            if regra.tipo_condicao == 'else':
                return regra.valor_frete

            if regra.tipo_condicao == 'if' or regra.tipo_condicao == 'elseif':
                if regra.avaliar_condicao(valor):
                    return regra.valor_frete

        # Se não encontrou nenhuma regra, retorna 0
        return Decimal('0.00')


class RegraFrete(models.Model):
    """
    Regra condicional de frete.
    Estrutura: SE valor <= X então frete = Y
    """
    TIPO_CONDICAO_CHOICES = [
        ('if', 'SE'),
        ('elseif', 'SENÃO SE'),
        ('else', 'SENÃO'),
    ]

    OPERADOR_CHOICES = [
        ('lte', '≤ (menor ou igual)'),
        ('lt', '< (menor que)'),
        ('gte', '≥ (maior ou igual)'),
        ('gt', '> (maior que)'),
        ('eq', '= (igual)'),
    ]

    tabela = models.ForeignKey(
        TabelaFrete,
        on_delete=models.CASCADE,
        related_name='regras',
        verbose_name='Tabela de Frete'
    )
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name='Ordem de Avaliação'
    )
    tipo_condicao = models.CharField(
        max_length=10,
        choices=TIPO_CONDICAO_CHOICES,
        default='if',
        verbose_name='Tipo de Condição'
    )
    operador = models.CharField(
        max_length=5,
        choices=OPERADOR_CHOICES,
        default='lte',
        verbose_name='Operador',
        blank=True
    )
    valor_limite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Valor Limite'
    )
    valor_frete = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Valor do Frete'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    class Meta:
        verbose_name = 'Regra de Frete'
        verbose_name_plural = 'Regras de Frete'
        ordering = ['tabela', 'ordem']

    def __str__(self):
        if self.tipo_condicao == 'else':
            return f"SENÃO → R$ {self.valor_frete}"
        operador_display = dict(self.OPERADOR_CHOICES).get(self.operador, self.operador)
        return f"{self.get_tipo_condicao_display()} valor {operador_display} {self.valor_limite} → R$ {self.valor_frete}"

    def clean(self):
        # Regra SENÃO não precisa de operador e valor_limite
        if self.tipo_condicao != 'else':
            if not self.operador:
                raise ValidationError('Operador é obrigatório para condições SE e SENÃO SE')
            if self.valor_limite is None:
                raise ValidationError('Valor limite é obrigatório para condições SE e SENÃO SE')

    def avaliar_condicao(self, valor):
        """Avalia se o valor satisfaz a condição desta regra"""
        if self.tipo_condicao == 'else':
            return True

        if self.valor_limite is None:
            return False

        operadores = {
            'lte': valor <= self.valor_limite,
            'lt': valor < self.valor_limite,
            'gte': valor >= self.valor_limite,
            'gt': valor > self.valor_limite,
            'eq': valor == self.valor_limite,
        }
        return operadores.get(self.operador, False)


class CanalVenda(models.Model):
    """
    Canal de venda (marketplace, loja própria, etc.)
    Pertence a um grupo e herda seus valores padrão.
    Pode ter frete fixo ou usar uma tabela de frete condicional.
    """
    TIPO_FRETE_CHOICES = [
        ('fixo', 'Frete Fixo'),
        ('tabela', 'Tabela de Frete'),
    ]

    nome = models.CharField(
        max_length=100,
        verbose_name='Nome do Canal'
    )
    grupo = models.ForeignKey(
        GrupoCanais,
        on_delete=models.PROTECT,
        related_name='canais',
        verbose_name='Grupo'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    # Flag para indicar se usa valores do grupo ou próprios
    herdar_grupo = models.BooleanField(
        default=True,
        verbose_name='Herdar valores do grupo',
        help_text='Se marcado, usa os percentuais definidos no grupo'
    )

    # Parâmetros do canal (podem sobrescrever o grupo)
    imposto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Imposto (%)'
    )
    operacao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Operação (%)'
    )
    lucro = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Lucro (%)'
    )
    promocao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Promoção (%)'
    )
    minimo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Mínimo (%)'
    )
    ads = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Ads (%)'
    )
    comissao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Comissão (%)'
    )

    # Configuração de frete
    tipo_frete = models.CharField(
        max_length=10,
        choices=TIPO_FRETE_CHOICES,
        default='fixo',
        verbose_name='Tipo de Frete'
    )
    frete_fixo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Frete Fixo (R$)'
    )
    tabela_frete = models.ForeignKey(
        TabelaFrete,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='canais',
        verbose_name='Tabela de Frete'
    )

    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Canal de Venda'
        verbose_name_plural = 'Canais de Venda'
        ordering = ['grupo', 'nome']
        unique_together = [['nome', 'grupo']]

    def __str__(self):
        return f"{self.nome} ({self.grupo.nome})"

    # Propriedades que retornam o valor efetivo (próprio ou herdado do grupo)
    def _get_valor_efetivo(self, campo):
        """Retorna o valor próprio ou herdado do grupo"""
        valor_proprio = getattr(self, campo)
        if self.herdar_grupo or valor_proprio is None:
            return getattr(self.grupo, campo)
        return valor_proprio

    @property
    def imposto_efetivo(self):
        return self._get_valor_efetivo('imposto')

    @property
    def operacao_efetivo(self):
        return self._get_valor_efetivo('operacao')

    @property
    def lucro_efetivo(self):
        return self._get_valor_efetivo('lucro')

    @property
    def promocao_efetivo(self):
        return self._get_valor_efetivo('promocao')

    @property
    def minimo_efetivo(self):
        return self._get_valor_efetivo('minimo')

    @property
    def ads_efetivo(self):
        return self._get_valor_efetivo('ads')

    @property
    def comissao_efetivo(self):
        return self._get_valor_efetivo('comissao')

    # Cálculos de Markup (conforme PRD)
    @property
    def markup_frete(self):
        """markup_frete = 100 * (1 / (100 - (imposto + ads + comissao)))"""
        denominador = Decimal('100') - (
            self.imposto_efetivo + self.ads_efetivo + self.comissao_efetivo
        )
        if denominador <= 0:
            return Decimal('0')
        return Decimal('100') * (Decimal('1') / denominador)

    @property
    def markup_venda(self):
        """markup_venda = 100 * (1 / (100 - (imposto + operacao + lucro + ads + comissao)))"""
        denominador = Decimal('100') - (
            self.imposto_efetivo + self.operacao_efetivo +
            self.lucro_efetivo + self.ads_efetivo + self.comissao_efetivo
        )
        if denominador <= 0:
            return Decimal('0')
        return Decimal('100') * (Decimal('1') / denominador)

    @property
    def markup_promocao(self):
        """markup_promocao = 100 * (1 / (100 - (imposto + operacao + promocao + ads + comissao)))"""
        denominador = Decimal('100') - (
            self.imposto_efetivo + self.operacao_efetivo +
            self.promocao_efetivo + self.ads_efetivo + self.comissao_efetivo
        )
        if denominador <= 0:
            return Decimal('0')
        return Decimal('100') * (Decimal('1') / denominador)

    @property
    def markup_minimo(self):
        """markup_minimo = 100 * (1 / (100 - (imposto + operacao + minimo + ads + comissao)))"""
        denominador = Decimal('100') - (
            self.imposto_efetivo + self.operacao_efetivo +
            self.minimo_efetivo + self.ads_efetivo + self.comissao_efetivo
        )
        if denominador <= 0:
            return Decimal('0')
        return Decimal('100') * (Decimal('1') / denominador)

    def obter_frete(self, peso_produto=None, preco_venda=None):
        """
        Retorna o valor do frete baseado no tipo configurado.
        Se frete fixo, retorna o valor fixo.
        Se tabela, calcula baseado no peso ou preço.
        """
        if self.tipo_frete == 'fixo':
            return self.frete_fixo

        if self.tabela_frete:
            if self.tabela_frete.tipo == 'peso' and peso_produto is not None:
                return self.tabela_frete.calcular_frete(peso_produto)
            elif self.tabela_frete.tipo == 'preco' and preco_venda is not None:
                return self.tabela_frete.calcular_frete(preco_venda)

        return Decimal('0.00')

    def clean(self):
        """Validações do canal"""
        # Se tipo frete é tabela, deve ter uma tabela selecionada
        if self.tipo_frete == 'tabela' and not self.tabela_frete:
            raise ValidationError(
                'Quando o tipo de frete é "Tabela", é necessário selecionar uma tabela de frete'
            )

        # Validar soma dos percentuais se não herdar do grupo
        if not self.herdar_grupo:
            valores = [
                self.imposto or Decimal('0'),
                self.operacao or Decimal('0'),
                self.lucro or Decimal('0'),
                self.promocao or Decimal('0'),
                self.ads or Decimal('0'),
                self.comissao or Decimal('0'),
            ]
            total = sum(valores)
            if total >= Decimal('100'):
                raise ValidationError(
                    'A soma dos percentuais não pode ser igual ou maior que 100%'
                )

            # Promoção deve ser >= mínimo
            promocao = self.promocao or Decimal('0')
            minimo = self.minimo or Decimal('0')
            if promocao < minimo:
                raise ValidationError(
                    'O percentual de promoção não pode ser menor que o percentual mínimo'
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
