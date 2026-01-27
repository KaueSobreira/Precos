from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP

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
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _calcular_preco_iterativo(self, canal, markup_target, frete_fixo=None, max_iteracoes=10, custo_base=None):
        # Resolve: Preço = (Custo + Taxa(Preço)) * Markup + Frete(Peso, Preço) * Markup_Frete
        peso = self.peso_produto
        custo = custo_base if custo_base is not None else self.custo

        preco_venda = Decimal('0.00')
        frete = frete_fixo if frete_fixo is not None else canal.obter_frete(
            peso_produto=peso,
            largura=self.largura,
            altura=self.altura,
            profundidade=self.profundidade
        )
        taxa = Decimal('0.00')

        for _ in range(max_iteracoes):
            novo_preco = ((custo + taxa) * markup_target) + (frete * canal.markup_frete)
            novo_preco = novo_preco.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)

            nova_taxa = canal.obter_taxa_extra(preco_venda=novo_preco)
            novo_frete = frete_fixo if frete_fixo is not None else canal.obter_frete(
                peso_produto=peso,
                preco_venda=novo_preco,
                largura=self.largura,
                altura=self.altura,
                profundidade=self.profundidade
            )

            # Previne oscilação: se o frete caiu para 0 (nenhuma regra cobriu o
            # preço calculado) mas antes era positivo, mantém o frete anterior.
            # Isso ocorre quando o preço + frete ultrapassa a faixa máxima da tabela.
            if frete_fixo is None and novo_frete == Decimal('0.00') and frete > Decimal('0.00'):
                novo_frete = frete

            if novo_preco == preco_venda and nova_taxa == taxa and novo_frete == frete:
                break

            preco_venda = novo_preco
            taxa = nova_taxa
            frete = novo_frete

        return preco_venda, frete, taxa

    def calcular_preco_venda(self, canal, frete=None, custo_base=None):
        preco, _, _ = self._calcular_preco_iterativo(canal, canal.markup_venda, frete_fixo=frete, custo_base=custo_base)
        return preco

    def calcular_preco_promocao(self, canal, frete=None, custo_base=None):
        preco, _, _ = self._calcular_preco_iterativo(canal, canal.markup_promocao, frete_fixo=frete, custo_base=custo_base)
        return preco

    def calcular_preco_minimo(self, canal, frete=None, custo_base=None):
        preco, _, _ = self._calcular_preco_iterativo(canal, canal.markup_minimo, frete_fixo=frete, custo_base=custo_base)
        return preco


class TituloProduto(models.Model):
    """
    Títulos alternativos de um produto.
    Cada título herda todas as propriedades do produto pai (dimensões, peso, custo, preços).
    Útil para anúncios diferentes do mesmo produto em marketplaces.
    """
    produto = models.ForeignKey(Produto, related_name='titulos', on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255, verbose_name='Título')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Título de Produto'
        verbose_name_plural = 'Títulos de Produtos'
        ordering = ['produto', 'titulo']

    def __str__(self):
        return f"{self.produto.sku} - {self.titulo}"

    # ========================================
    # Propriedades herdadas do produto pai
    # ========================================

    @property
    def produto_pai(self):
        """Retorna o produto pai."""
        return self.produto

    @property
    def sku_pai(self):
        """SKU do produto pai."""
        return self.produto.sku

    @property
    def titulo_pai(self):
        """Título do produto pai."""
        return self.produto.titulo

    @property
    def largura(self):
        """Largura herdada do produto pai."""
        return self.produto.largura

    @property
    def altura(self):
        """Altura herdada do produto pai."""
        return self.produto.altura

    @property
    def profundidade(self):
        """Profundidade herdada do produto pai."""
        return self.produto.profundidade

    @property
    def peso_fisico(self):
        """Peso físico herdado do produto pai."""
        return self.produto.peso_fisico

    @property
    def peso_cubico(self):
        """Peso cúbico calculado a partir das dimensões do pai."""
        return self.produto.peso_cubico

    @property
    def peso_produto(self):
        """Peso do produto (maior entre físico e cúbico)."""
        return self.produto.peso_produto

    @property
    def custo(self):
        """Custo herdado do produto pai (soma da ficha técnica)."""
        return self.produto.custo

    @property
    def itens_ficha(self):
        """Itens da ficha técnica do produto pai."""
        return self.produto.itens_ficha

    @property
    def precos_canais(self):
        """Preços por canal do produto pai."""
        return self.produto.precos_canais

    def get_preco_canal(self, canal):
        """Retorna o preço do produto pai para um canal específico."""
        try:
            return self.produto.precos_canais.get(canal=canal, ativo=True)
        except PrecoProdutoCanal.DoesNotExist:
            return None

    def calcular_preco_venda(self, canal, frete=None):
        """Calcula preço de venda usando o produto pai."""
        return self.produto.calcular_preco_venda(canal, frete)

    def calcular_preco_promocao(self, canal, frete=None):
        """Calcula preço promocional usando o produto pai."""
        return self.produto.calcular_preco_promocao(canal, frete)

    def calcular_preco_minimo(self, canal, frete=None):
        """Calcula preço mínimo usando o produto pai."""
        return self.produto.calcular_preco_minimo(canal, frete)


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
        return (self.quantidade * self.custo_unitario * self.multiplicador).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)

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
    preco_promocao_arredondado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preco Promo Arredondado')
    preco_minimo_arredondado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Preco Min Arredondado')
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
        return self.canal.obter_frete(
            peso_produto=self.produto.peso_produto, 
            preco_venda=self.preco_venda,
            largura=self.produto.largura,
            altura=self.produto.altura,
            profundidade=self.produto.profundidade
        )

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

    def _obter_custo_base_grupo(self):
        """Determina o custo base seguindo a estratégia do grupo."""
        grupo = self.canal.grupo
        if grupo and grupo.tipo_custo == 'canal' and grupo.canal_referencia_custo:
            try:
                # Evita recursão se o canal de referência for o mesmo
                if grupo.canal_referencia_custo.pk != self.canal.pk:
                    preco_ref = PrecoProdutoCanal.objects.filter(
                        produto=self.produto,
                        canal=grupo.canal_referencia_custo,
                        ativo=True
                    ).first()
                    
                    if preco_ref:
                        # Recalcula on-the-fly para obter precisão total (6 casas)
                        # em vez de usar o valor arredondado do banco (2 casas)
                        pv, _, _, _, _, _ = preco_ref._calcular_todos_precos()
                        if pv > 0:
                            return pv
            except Exception:
                pass 
        return self.produto.custo

    @property
    def custo(self):
        """Retorna o custo (calculado ou do produto), considerando a estratégia do grupo."""
        if self.custo_calculado is not None:
            return self.custo_calculado
        return self._obter_custo_base_grupo()

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
        return ((self.preco_venda - self.preco_minimo) / self.preco_venda * Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def _arredondar_preco(valor):
        """
        Arredondamento comercial (replica formula Excel):
        =SE(VALOR(DIREITA(TEXTO(val;"0,00");2))<50; INT(val)-0,1; ARRED(val;1))

        Se centavos < 50: piso do valor - 0,10  (ex: 52.30 -> 51.90)
        Se centavos >= 50: arredonda p/ 1 casa   (ex: 52.97 -> 53.00)
        """
        if valor is None or valor <= 0:
            return valor
        centavos = int((valor % 1) * 100)
        if centavos < 50:
            return Decimal(int(valor)) - Decimal('0.10')
        else:
            return valor.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

    @property
    def preco_promocao_arred(self):
        """Retorna o preco promocional arredondado (armazenado ou calculado)."""
        if self.preco_promocao_arredondado is not None:
            return self.preco_promocao_arredondado
        return self._arredondar_preco(self.preco_promocao)

    @property
    def preco_minimo_arred(self):
        """Retorna o preco minimo arredondado (armazenado ou calculado)."""
        if self.preco_minimo_arredondado is not None:
            return self.preco_minimo_arredondado
        return self._arredondar_preco(self.preco_minimo)

    def salvar_historico(self, usuario=None, motivo=''):
        """Salva um snapshot imutável dos preços atuais com todos os parâmetros."""
        canal = self.canal

        HistoricoPreco.objects.create(
            # Identificação
            produto=self.produto,
            canal=canal,
            grupo_nome=canal.grupo.nome if canal.grupo else '',
            usuario=usuario,
            motivo=motivo,

            # Valores do Produto
            custo=self.custo,
            peso_produto=self.produto.peso_produto,

            # Preços Calculados
            preco_venda=self.preco_venda,
            preco_promocao=self.preco_promocao,
            preco_minimo=self.preco_minimo,
            frete_aplicado=self.frete_aplicado,
            taxa_extra=self.taxa_extra,

            # Parâmetros (%) - snapshot do canal
            imposto=canal.imposto_efetivo,
            operacao=canal.operacao_efetivo,
            lucro=canal.lucro_efetivo,
            promocao=canal.promocao_efetivo,
            minimo=canal.minimo_efetivo,
            ads=canal.ads_efetivo,
            comissao=canal.comissao_efetivo,

            # Markups
            markup_frete=canal.markup_frete,
            markup_venda=canal.markup_venda,
            markup_promocao=canal.markup_promocao,
            markup_minimo=canal.markup_minimo,
        )

    def _calcular_todos_precos(self):
        """
        Calcula preco_venda, preco_promocao, preco_minimo, frete e taxa.
        Se a tabela de frete do canal usa usar_preco_promocao, o frete e calculado
        com base no preco promocional convergido, e esse frete fixo e usado para
        calcular preco_venda e preco_minimo.
        """
        frete_base = self.frete_especifico
        canal = self.canal
        
        # Determina o custo base (pode vir de outro canal)
        custo = self._obter_custo_base_grupo()

        usar_preco_promo = (
            frete_base is None
            and canal.tipo_frete == 'tabela'
            and canal.tabela_frete
            and canal.tabela_frete.usar_preco_promocao
        )

        if usar_preco_promo:
            # 1. Calcula preco_promocao primeiro (frete itera normalmente)
            preco_promocao, frete_promo, _ = self.produto._calcular_preco_iterativo(
                canal, canal.markup_promocao, frete_fixo=None, custo_base=custo
            )

            # 2. Usa o frete convergido do promo para calcular os demais precos
            preco_venda = self.produto.calcular_preco_venda(canal, frete=frete_promo, custo_base=custo)
            preco_minimo = self.produto.calcular_preco_minimo(canal, frete=frete_promo, custo_base=custo)
            frete = frete_promo
        else:
            # Calculo normal - usa frete convergido do preco_venda
            preco_venda, frete_iter, _ = self.produto._calcular_preco_iterativo(
                canal, canal.markup_venda, frete_fixo=frete_base, custo_base=custo
            )
            preco_promocao = self.produto.calcular_preco_promocao(canal, frete_base, custo_base=custo)
            preco_minimo = self.produto.calcular_preco_minimo(canal, frete_base, custo_base=custo)
            frete = frete_base if frete_base is not None else frete_iter

        # O custo armazenado deve ser o que foi usado no cálculo
        # custo já está definido acima
        taxa = canal.obter_taxa_extra(preco_venda=preco_venda)

        return preco_venda, preco_promocao, preco_minimo, frete, taxa, custo

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
        preco_venda, preco_promocao, preco_minimo, frete, taxa, custo = self._calcular_todos_precos()

        # Atualiza os campos calculados
        self.custo_calculado = custo
        self.preco_venda_calculado = preco_venda
        self.preco_promocao_calculado = preco_promocao
        self.preco_minimo_calculado = preco_minimo
        self.preco_promocao_arredondado = self._arredondar_preco(preco_promocao)
        self.preco_minimo_arredondado = self._arredondar_preco(preco_minimo)
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

            preco_venda, preco_promocao, preco_minimo, frete, taxa, custo = self._calcular_todos_precos()

            self.custo_calculado = custo
            self.preco_venda_calculado = preco_venda
            self.preco_promocao_calculado = preco_promocao
            self.preco_minimo_calculado = preco_minimo
            self.preco_promocao_arredondado = self._arredondar_preco(preco_promocao)
            self.preco_minimo_arredondado = self._arredondar_preco(preco_minimo)
            self.frete_calculado = frete
            self.taxa_calculada = taxa
            self.calculado_em = timezone.now()

        super().save(*args, **kwargs)

class HistoricoPreco(models.Model):
    """
    Registro imutável de preços.
    Captura snapshot completo: preços, parâmetros e markups no momento da alteração.
    """
    # Identificação
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, related_name='historicos')
    canal = models.ForeignKey(CanalVenda, on_delete=models.SET_NULL, null=True)
    grupo_nome = models.CharField(max_length=100, blank=True, verbose_name='Grupo')
    data_registro = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    motivo = models.TextField(blank=True)

    # Valores do Produto
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    peso_produto = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)

    # Preços Calculados
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    preco_promocao = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preco_minimo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    frete_aplicado = models.DecimalField(max_digits=10, decimal_places=2)
    taxa_extra = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Parâmetros (%) - snapshot do canal no momento
    imposto = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    operacao = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    lucro = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    promocao = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    minimo = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ads = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    comissao = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Markups - snapshot calculado no momento
    markup_frete = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    markup_venda = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    markup_promocao = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    markup_minimo = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    class Meta:
        verbose_name = 'Histórico de Preço'
        verbose_name_plural = 'Históricos de Preços'
        ordering = ['-data_registro']

    def __str__(self):
        return f"{self.produto} - {self.canal} - {self.data_registro:%d/%m/%Y %H:%M}"