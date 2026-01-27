from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Componente(models.Model):
    nome = models.CharField(max_length=200, unique=True, verbose_name="Nome do Material/Serviço")
    preco = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Preço Padrão (R$)"
    )
    
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Componente (PCP)"
        verbose_name_plural = "Componentes (PCP)"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"