from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class TabelaFrete(models.Model):
    TIPO_CHOICES = [
        ('peso', 'Por Peso (kg)'),
        ('preco', 'Por Preço (R$)'),
        ('matriz', 'Matriz Peso × Preço'),
    ]

    nome = models.CharField(max_length=100, unique=True, verbose_name='Nome da Tabela')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='matriz')
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    suporta_nota_vendedor = models.BooleanField(default=False, verbose_name='Desconto por Nota')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tabela de Frete'
        verbose_name_plural = 'Tabelas de Frete'

    def __str__(self):
        return self.nome

    def calcular_frete(self, peso=None, preco=None, nota_vendedor=None):
        """
        Calcula o frete.
        1. Identifica o tipo (Matriz, Peso ou Preço).
        2. Busca a regra correspondente.
        3. Aplica desconto de nota se aplicável.
        """
        if peso is None: peso = Decimal('0.000')
        if preco is None: preco = Decimal('0.00')

        valor_frete = Decimal('0.00')

        if self.tipo == 'matriz':
            valor_frete = self._calcular_matriz(peso, preco)
        elif self.tipo == 'peso':
            valor_frete = self._calcular_simples(peso)
        elif self.tipo == 'preco':
            valor_frete = self._calcular_simples(preco)

        # Aplica desconto por nota se existir e se o canal tiver nota
        if self.suporta_nota_vendedor and nota_vendedor:
            try:
                desc = self.descontos_nota.filter(nota=nota_vendedor).first()
                if desc:
                    fator = (Decimal('100') - desc.percentual_desconto) / Decimal('100')
                    valor_frete = (valor_frete * fator).quantize(Decimal('0.01'))
            except Exception:
                pass

        return valor_frete

    def _calcular_matriz(self, peso, preco):
        regras = self.regras_matriz.filter(ativo=True).order_by('ordem', 'peso_inicio', 'preco_inicio')
        for regra in regras:
            if regra.avaliar_condicao(peso, preco):
                return regra.valor_frete
        return Decimal('0.00')

    def _calcular_simples(self, valor_teste):
        """Busca regra para tabelas de Peso ou Preço (1 dimensão)"""
        regras = self.regras_simples.filter(ativo=True).order_by('inicio')
        for regra in regras:
            if regra.avaliar_condicao(valor_teste):
                return regra.valor_frete
        return Decimal('0.00')


class RegraFreteMatriz(models.Model):
    """Regra 2D: Peso x Preço"""
    tabela = models.ForeignKey(TabelaFrete, related_name='regras_matriz', on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField(default=0)
    
    peso_inicio = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Peso Início')
    peso_fim = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Peso Fim')
    preco_inicio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preço Início')
    preco_fim = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preço Fim')
    
    valor_frete = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Frete')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Regra Matriz (Peso x Preço)'
        verbose_name_plural = 'Regras Matriz'
        ordering = ['tabela', 'ordem']

    def save(self, *args, **kwargs):
        if self.peso_inicio is None: self.peso_inicio = Decimal('0.000')
        if self.preco_inicio is None: self.preco_inicio = Decimal('0.00')
        super().save(*args, **kwargs)

    def avaliar_condicao(self, peso, preco):
        p_ini = self.peso_inicio or Decimal('0.000')
        pr_ini = self.preco_inicio or Decimal('0.00')

        if peso < p_ini or preco < pr_ini: return False
        if self.peso_fim is not None and peso >= self.peso_fim: return False
        if self.preco_fim is not None and preco >= self.preco_fim: return False
        return True


class RegraFreteSimples(models.Model):
    """
    Regra 1D: Apenas Peso OU Apenas Preço.
    Usada quando o TabelaFrete.tipo é 'peso' ou 'preco'.
    """
    tabela = models.ForeignKey(TabelaFrete, related_name='regras_simples', on_delete=models.CASCADE)
    
    inicio = models.DecimalField(
        max_digits=10, decimal_places=3, 
        null=True, blank=True, 
        verbose_name='Início (Kg ou R$)'
    )
    fim = models.DecimalField(
        max_digits=10, decimal_places=3, 
        null=True, blank=True, 
        verbose_name='Fim (Kg ou R$)'
    )
    
    valor_frete = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Frete')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Regra Simples (Peso ou Preço)'
        verbose_name_plural = 'Regras Simples'
        ordering = ['tabela', 'inicio']

    def save(self, *args, **kwargs):
        if self.inicio is None: self.inicio = Decimal('0.000')
        super().save(*args, **kwargs)

    def avaliar_condicao(self, valor):
        # Lógica [Inicio, Fim)
        ini = self.inicio or Decimal('0.000')
        
        if valor < ini:
            return False
        
        if self.fim is not None:
            if valor >= self.fim:
                return False
        
        return True


class TabelaTaxa(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    ativo = models.BooleanField(default=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome

    def calcular_taxa(self, preco):
        if preco is None: preco = Decimal('0.00')
        regras = self.regras.filter(ativo=True).order_by('preco_inicio')
        for regra in regras:
            if regra.avaliar(preco):
                return regra.valor_taxa
        return Decimal('0.00')

class RegraTaxa(models.Model):
    tabela = models.ForeignKey(TabelaTaxa, related_name='regras', on_delete=models.CASCADE)
    preco_inicio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_fim = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_taxa = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.preco_inicio is None: self.preco_inicio = Decimal('0.00')
        super().save(*args, **kwargs)

    def avaliar(self, preco):
        ini = self.preco_inicio or Decimal('0.00')
        if preco < ini: return False
        if self.preco_fim is not None and preco >= self.preco_fim: return False
        return True

class DescontoNotaVendedor(models.Model):
    tabela = models.ForeignKey(TabelaFrete, related_name='descontos_nota', on_delete=models.CASCADE)
    nota = models.PositiveSmallIntegerField(
        choices=[(1,'1'),(2,'2'),(3,'3'),(4,'4'),(5,'5')],
        verbose_name='Nota'
    )
    percentual_desconto = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    class Meta:
        unique_together = [['tabela', 'nota']]
        ordering = ['nota']