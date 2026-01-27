from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class TabelaFrete(models.Model):
    TIPO_CHOICES = [
        ('peso', 'Por Peso (kg)'),
        ('preco', 'Por Preço (R$)'),
        ('matriz', 'Matriz Peso × Preço'),
        ('matriz_score', 'Matriz Peso × Score'),
    ]

    nome = models.CharField(max_length=100, unique=True, verbose_name='Nome da Tabela')
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, default='matriz')
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    suporta_nota_vendedor = models.BooleanField(default=False, verbose_name='Desconto por Nota')
    
    # Nova Taxa Fixa na Tabela
    adicionar_taxa_fixa = models.BooleanField(default=False, verbose_name='Adicionar Taxa Fixa')
    valor_taxa_fixa = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name='Valor da Taxa Fixa')

    # Nova Lógica: Acima de 1 Metro
    usa_tabela_excedente = models.BooleanField(default=False, verbose_name='Tabela Diferenciada > 1m')

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tabela de Frete'
        verbose_name_plural = 'Tabelas de Frete'

    def __str__(self):
        return self.nome

    def calcular_frete(self, peso=None, preco=None, nota_vendedor=None, largura=0, altura=0, profundidade=0, score=None):
        """
        Calcula o frete.
        """
        if peso is None: peso = Decimal('0.000')
        if preco is None: preco = Decimal('0.00')
        
        # 0. Verifica Regras Especiais (Prioridade Máxima)
        # Ex: Se peso > 30kg ou dimensões > X, usa valor fixo especial
        regras_especiais = self.regras_especiais.filter(ativo=True).order_by('ordem')
        for regra in regras_especiais:
            if regra.avaliar_condicao(largura, altura, profundidade, peso):
                return regra.valor_frete

        # 1. Verifica se é excedente (> 100cm em qualquer dimensão)
        # Só ativa a flag se a tabela estiver configurada para usar tabela excedente
        eh_excedente = False
        if self.usa_tabela_excedente:
            if largura > 100 or altura > 100 or profundidade > 100:
                eh_excedente = True

        valor_frete = Decimal('0.00')

        if self.tipo == 'matriz':
            valor_frete = self._calcular_matriz(peso, preco, eh_excedente)
        elif self.tipo == 'matriz_score':
            valor_frete = self._calcular_matriz_score(peso, score, eh_excedente)
        elif self.tipo == 'peso':
            valor_frete = self._calcular_simples(peso, eh_excedente)
        elif self.tipo == 'preco':
            valor_frete = self._calcular_simples(preco, eh_excedente)

        # Aplica desconto por nota se existir e se o canal tiver nota
        if self.suporta_nota_vendedor and nota_vendedor:
            try:
                desc = self.descontos_nota.filter(nota=nota_vendedor).first()
                if desc:
                    fator = (Decimal('100') - desc.percentual_desconto) / Decimal('100')
                    valor_frete = (valor_frete * fator).quantize(Decimal('0.01'))
            except Exception:
                pass
        
        # Adiciona Taxa Fixa se habilitada (conforme pedido: valor -> desconto -> soma taxa)
        if self.adicionar_taxa_fixa:
            valor_frete += self.valor_taxa_fixa

        return valor_frete

    def _calcular_matriz(self, peso, preco, excedente):
        regras = self.regras_matriz.filter(ativo=True, excedente=excedente).order_by('ordem', 'peso_inicio', 'preco_inicio')
        for regra in regras:
            if regra.avaliar_condicao(peso, preco=preco):
                return regra.valor_frete
        return Decimal('0.00')

    def _calcular_matriz_score(self, peso, score, excedente):
        if score is None: score = 0
        regras = self.regras_matriz.filter(ativo=True, excedente=excedente).order_by('ordem', 'peso_inicio', 'score_inicio')
        for regra in regras:
            if regra.avaliar_condicao(peso, score=score):
                return regra.valor_frete
        return Decimal('0.00')

    def _calcular_simples(self, valor_teste, excedente):
        """Busca regra para tabelas de Peso ou Preço (1 dimensão)"""
        regras = self.regras_simples.filter(ativo=True, excedente=excedente).order_by('inicio')
        for regra in regras:
            if regra.avaliar_condicao(valor_teste):
                return regra.valor_frete
        return Decimal('0.00')


class RegraFreteEspecial(models.Model):
    """
    Regra Especial de Frete (Prioridade sobre as outras).
    Define condições mínimas de dimensões ou peso para aplicar um valor fixo.
    Se todas as condições definidas na regra forem atendidas, o frete é aplicado.
    """
    tabela = models.ForeignKey(TabelaFrete, related_name='regras_especiais', on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField(default=0)
    
    largura_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Largura Mín (cm)')
    altura_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Altura Mín (cm)')
    profundidade_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Profundidade Mín (cm)')
    peso_min = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Peso Mín (kg)')
    
    valor_frete = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Frete')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Regra Especial'
        verbose_name_plural = 'Regras Especiais'
        ordering = ['tabela', 'ordem']

    def avaliar_condicao(self, largura, altura, profundidade, peso):
        # Se o campo estiver preenchido, a condição deve ser atendida
        if self.largura_min is not None and largura < self.largura_min:
            return False
        if self.altura_min is not None and altura < self.altura_min:
            return False
        if self.profundidade_min is not None and profundidade < self.profundidade_min:
            return False
        if self.peso_min is not None and peso < self.peso_min:
            return False
        
        return True


class RegraFreteMatriz(models.Model):
    """Regra 2D: Peso x Preço OU Peso x Score"""
    tabela = models.ForeignKey(TabelaFrete, related_name='regras_matriz', on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField(default=0)
    
    # Eixo 1: Peso
    peso_inicio = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Peso Início')
    peso_fim = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, verbose_name='Peso Fim')
    
    # Eixo 2: Preço
    preco_inicio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preço Início')
    preco_fim = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preço Fim')

    # Eixo 2: Score (Alternativa ao Preço)
    score_inicio = models.IntegerField(null=True, blank=True, verbose_name='Score Início')
    score_fim = models.IntegerField(null=True, blank=True, verbose_name='Score Fim')
    
    valor_frete = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Frete')
    
    # Flag para > 1m
    excedente = models.BooleanField(default=False, verbose_name='Regra Excedente (>1m)')
    
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Regra Matriz'
        verbose_name_plural = 'Regras Matriz'
        ordering = ['tabela', 'excedente', 'ordem']

    def save(self, *args, **kwargs):
        if self.peso_inicio is None: self.peso_inicio = Decimal('0.000')
        if self.preco_inicio is None: self.preco_inicio = Decimal('0.00')
        if self.score_inicio is None: self.score_inicio = 0
        super().save(*args, **kwargs)

    def avaliar_condicao(self, peso, preco=None, score=None):
        p_ini = self.peso_inicio or Decimal('0.000')
        
        # Avalia Peso
        if peso < p_ini: return False
        if self.peso_fim is not None and peso >= self.peso_fim: return False

        # Avalia Preço (se tabela for Matriz Preço)
        if preco is not None:
            pr_ini = self.preco_inicio or Decimal('0.00')
            if preco < pr_ini: return False
            if self.preco_fim is not None and preco >= self.preco_fim: return False

        # Avalia Score (se tabela for Matriz Score)
        if score is not None:
            s_ini = self.score_inicio or 0
            if score < s_ini: return False
            # Score é inclusivo no final (<=) pois é inteiro discreto
            if self.score_fim is not None and score > self.score_fim: return False

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
    
    # Flag para > 1m
    excedente = models.BooleanField(default=False, verbose_name='Regra Excedente (>1m)')
    
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Regra Simples (Peso ou Preço)'
        verbose_name_plural = 'Regras Simples'
        ordering = ['tabela', 'excedente', 'inicio']

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