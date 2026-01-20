from django.db import models
from django.core.validators import MinValueValidator
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
        if peso is None: peso = Decimal('0.000')
        if preco is None: preco = Decimal('0.00')

        # Busca na matriz
        regras = self.regras_matriz.filter(ativo=True).order_by('ordem', 'peso_inicio', 'preco_inicio')
        valor_frete = Decimal('0.00')

        for regra in regras:
            if regra.avaliar_condicao(peso, preco):
                valor_frete = regra.valor_frete
                break

        # Aplica desconto por nota se existir
        if self.suporta_nota_vendedor and nota_vendedor:
            try:
                desc = self.descontos_nota.get(nota=nota_vendedor)
                valor_frete = (valor_frete * (Decimal('100') - desc.percentual_desconto) / Decimal('100')).quantize(Decimal('0.01'))
            except:
                pass

        return valor_frete

class RegraFreteMatriz(models.Model):
    tabela = models.ForeignKey(TabelaFrete, related_name='regras_matriz', on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField(default=0)
    
    # SALVA TUDO: Permite null e blank para o usuário deixar vazio se não houver limite
    peso_inicio = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Peso Início')
    peso_fim = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Peso Fim')
    preco_inicio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preço Início')
    preco_fim = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preço Fim')
    
    valor_frete = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Frete')
    ativo = models.BooleanField(default=True)

    def avaliar_condicao(self, peso, preco):
        # Lógica: [Inicio, Fim) -> Fechado no inicio, Aberto no fim
        p_ini = self.peso_inicio if self.peso_inicio is not None else Decimal('0.000')
        pr_ini = self.preco_inicio if self.preco_inicio is not None else Decimal('0.00')

        # Verifica Início (Inclusivo)
        if peso < p_ini or preco < pr_ini:
            return False
        
        # Verifica Fim (Exclusivo)
        if self.peso_fim is not None and peso >= self.peso_fim:
            return False
        if self.preco_fim is not None and preco >= self.preco_fim:
            return False
            
        return True

    class Meta:
        verbose_name = 'Regra Matriz'
        verbose_name_plural = 'Regras Matriz'

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

    def avaliar(self, preco):
        # Lógica: [Inicio, Fim) 
        ini = self.preco_inicio if self.preco_inicio is not None else Decimal('0.00')
        if preco < ini:
            return False
        if self.preco_fim is not None and preco >= self.preco_fim:
            return False
        return True

class DescontoNotaVendedor(models.Model):
    tabela = models.ForeignKey(TabelaFrete, related_name='descontos_nota', on_delete=models.CASCADE)
    nota = models.PositiveSmallIntegerField()
    percentual_desconto = models.DecimalField(max_digits=5, decimal_places=2)
