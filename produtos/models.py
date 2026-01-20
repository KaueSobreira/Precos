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

    # Preços manuais (usados quando usar_calculo_automatico=False)
    preco_venda_manual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_promocao_manual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_minimo_manual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Campos calculados (salvos no banco para performance)
    preco_venda_calculado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_promocao_calculado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_minimo_calculado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    frete_calculado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custo_calculado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taxa_calculada = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    calculado_em = models.DateTimeField(null=True, blank=True, verbose_name='Última atualização do cálculo')

    frete_especifico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        unique_together = ['produto', 'canal']
        verbose_name = 'Preço Produto/Canal'
        verbose_name_plural = 'Preços Produto/Canal'

    def __str__(self):
        return f"{self.produto.sku} - {self.canal.nome}"

    @property
    def frete_aplicado(self):
        """Retorna o frete específico ou o calculado."""
        if self.frete_especifico is not None:
            return self.frete_especifico
        if self.frete_calculado is not None:
            return self.frete_calculado
        # Fallback: calcula em tempo real
        return self.canal.obter_frete(peso_produto=self.produto.peso_produto, preco_venda=self.preco_venda)

    @property
    def preco_venda(self):
        """Retorna o preço de venda (manual ou calculado)."""
        if not self.usar_calculo_automatico and self.preco_venda_manual:
            return self.preco_venda_manual
        if self.preco_venda_calculado is not None:
            return self.preco_venda_calculado
        # Fallback: calcula em tempo real
        return self.produto.calcular_preco_venda(self.canal, self.frete_especifico)

    @property
    def preco_promocao(self):
        """Retorna o preço promocional (manual ou calculado)."""
        if not self.usar_calculo_automatico and self.preco_promocao_manual:
            return self.preco_promocao_manual
        if self.preco_promocao_calculado is not None:
            return self.preco_promocao_calculado
        # Fallback: calcula em tempo real
        return self.produto.calcular_preco_promocao(self.canal, self.frete_especifico)

    @property
    def preco_minimo(self):
        """Retorna o preço mínimo (manual ou calculado)."""
        if not self.usar_calculo_automatico and self.preco_minimo_manual:
            return self.preco_minimo_manual
        if self.preco_minimo_calculado is not None:
            return self.preco_minimo_calculado
        # Fallback: calcula em tempo real
        return self.produto.calcular_preco_minimo(self.canal, self.frete_especifico)

    @property
    def custo(self):
        """Retorna o custo (calculado ou do produto)."""
        if self.custo_calculado is not None:
            return self.custo_calculado
        return self.produto.custo

    @property
    def taxa_extra(self):
        """Retorna a taxa extra calculada."""
        if self.taxa_calculada is not None:
            return self.taxa_calculada
        return self.canal.obter_taxa_extra(self.preco_venda)

    @property
    def desconto_maximo_percentual(self):
        """Calcula o desconto máximo possível."""
        if self.preco_venda <= 0:
            return Decimal('0.00')
        return ((self.preco_venda - self.preco_minimo) / self.preco_venda * Decimal('100')).quantize(Decimal('0.01'))

    def salvar_historico(self, usuario=None, motivo=''):
        """Salva um snapshot imutável dos preços atuais."""
        HistoricoPreco.objects.create(
            produto=self.produto,
            canal=self.canal,
            custo=self.custo,
            preco_venda=self.preco_venda,
            preco_promocao=self.preco_promocao,
            preco_minimo=self.preco_minimo,
            frete_aplicado=self.frete_aplicado,
            taxa_extra=self.taxa_extra,
            usuario=usuario,
            motivo=motivo
        )

    def recalcular_precos(self, salvar_historico=True, usuario=None, motivo='Recálculo automático'):
        """
        Recalcula todos os preços e salva no banco.
        Se salvar_historico=True, salva os preços antigos no histórico antes de atualizar.
        """
        from django.utils import timezone

        # Salva histórico com preços antigos (apenas se já tiver preços calculados)
        if salvar_historico and self.preco_venda_calculado is not None:
            self.salvar_historico(usuario=usuario, motivo=motivo)

        # Recalcula todos os valores
        custo = self.produto.custo
        peso = self.produto.peso_produto
        frete_base = self.frete_especifico

        # Calcula preços usando o algoritmo iterativo
        preco_venda = self.produto.calcular_preco_venda(self.canal, frete_base)
        preco_promocao = self.produto.calcular_preco_promocao(self.canal, frete_base)
        preco_minimo = self.produto.calcular_preco_minimo(self.canal, frete_base)

        # Calcula frete e taxa baseados no preço de venda
        if frete_base is not None:
            frete = frete_base
        else:
            frete = self.canal.obter_frete(peso_produto=peso, preco_venda=preco_venda)
        taxa = self.canal.obter_taxa_extra(preco_venda=preco_venda)

        # Atualiza os campos calculados
        self.custo_calculado = custo
        self.preco_venda_calculado = preco_venda
        self.preco_promocao_calculado = preco_promocao
        self.preco_minimo_calculado = preco_minimo
        self.frete_calculado = frete
        self.taxa_calculada = taxa
        self.calculado_em = timezone.now()

        # Salva sem disparar o save() normal (evita loop)
        self.save(recalculando=True)

        return self

    @transaction.atomic
    def save(self, *args, recalculando=False, **kwargs):
        # Se é um update normal (não recálculo), salva histórico
        if self.pk and not recalculando:
            # Verifica se já tem preços calculados para salvar no histórico
            if self.preco_venda_calculado is not None:
                self.salvar_historico(motivo='Alteração manual')

        # Se é criação ou alteração manual, recalcula os preços
        if not recalculando:
            from django.utils import timezone
            custo = self.produto.custo
            peso = self.produto.peso_produto
            frete_base = self.frete_especifico

            preco_venda = self.produto.calcular_preco_venda(self.canal, frete_base)
            preco_promocao = self.produto.calcular_preco_promocao(self.canal, frete_base)
            preco_minimo = self.produto.calcular_preco_minimo(self.canal, frete_base)

            if frete_base is not None:
                frete = frete_base
            else:
                frete = self.canal.obter_frete(peso_produto=peso, preco_venda=preco_venda)
            taxa = self.canal.obter_taxa_extra(preco_venda=preco_venda)

            self.custo_calculado = custo
            self.preco_venda_calculado = preco_venda
            self.preco_promocao_calculado = preco_promocao
            self.preco_minimo_calculado = preco_minimo
            self.frete_calculado = frete
            self.taxa_calculada = taxa
            self.calculado_em = timezone.now()

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