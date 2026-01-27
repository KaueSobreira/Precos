import uuid
from django.db import models


class ApiKey(models.Model):
    key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name='Chave')
    name = models.CharField(max_length=100, verbose_name='Nome')
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')

    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'

    def __str__(self):
        return f"{self.name} ({'ativa' if self.is_active else 'inativa'})"
