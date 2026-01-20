from django.apps import AppConfig


class ProdutosConfig(AppConfig):
    name = 'produtos'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        # Importa signals para registrá-los
        import produtos.signals  # noqa: F401
