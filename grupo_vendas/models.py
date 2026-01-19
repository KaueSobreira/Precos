from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class GrupoCanais(models.Model):
    """
    Grupo de canais de venda (Ecossistema).
    Define valores padrão que são herdados pelos canais pertencentes ao grupo.
    """
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome do Grupo'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='Grupo Padrão',
        help_text='O grupo ECOSSISTEMA é o padrão e não pode ser removido'
    )

    # Parâmetros padrão do grupo (herdados pelos canais)
    imposto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Imposto (%)'
    )
    operacao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Operação (%)'
    )
    lucro = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Lucro (%)'
    )
    promocao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Promoção (%)'
    )
    minimo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Mínimo (%)'
    )
    ads = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Ads (%)'
    )
    comissao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('99.99'))],
        verbose_name='Comissão (%)'
    )

    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Grupo de Canais'
        verbose_name_plural = 'Grupos de Canais'
        ordering = ['-is_default', 'nome']

    def __str__(self):
        return self.nome

    def clean(self):
        """Valida que a soma dos percentuais não ultrapasse 100%"""
        total = (
            self.imposto + self.operacao + self.lucro +
            self.promocao + self.ads + self.comissao
        )
        if total >= Decimal('100'):
            raise ValidationError(
                'A soma dos percentuais não pode ser igual ou maior que 100%'
            )

        # Promoção deve ser >= mínimo
        if self.promocao < self.minimo:
            raise ValidationError(
                'O percentual de promoção não pode ser menor que o percentual mínimo'
            )

    def delete(self, *args, **kwargs):
        """Impede a exclusão do grupo ECOSSISTEMA"""
        if self.is_default:
            raise ValidationError('O grupo padrão ECOSSISTEMA não pode ser removido')
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
