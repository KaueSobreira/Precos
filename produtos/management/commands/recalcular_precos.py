"""
Comando para recalcular todos os preços em lote.

Uso:
    python manage.py recalcular_precos                    # Recalcula todos
    python manage.py recalcular_precos --produto SKU123   # Apenas um produto
    python manage.py recalcular_precos --canal "ML Full"  # Apenas um canal
    python manage.py recalcular_precos --sem-historico    # Sem salvar histórico
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from produtos.models import Produto, PrecoProdutoCanal
from canais_vendas.models import CanalVenda


class Command(BaseCommand):
    help = 'Recalcula todos os preços dos produtos em todos os canais'

    def add_arguments(self, parser):
        parser.add_argument(
            '--produto',
            type=str,
            help='SKU do produto específico para recalcular',
        )
        parser.add_argument(
            '--canal',
            type=str,
            help='Nome do canal específico para recalcular',
        )
        parser.add_argument(
            '--sem-historico',
            action='store_true',
            help='Não salvar histórico (útil para migração inicial)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria feito, sem executar',
        )

    def handle(self, *args, **options):
        sku = options.get('produto')
        canal_nome = options.get('canal')
        sem_historico = options.get('sem_historico', False)
        dry_run = options.get('dry_run', False)

        # Filtra os preços
        precos = PrecoProdutoCanal.objects.filter(ativo=True)

        if sku:
            try:
                produto = Produto.objects.get(sku=sku)
                precos = precos.filter(produto=produto)
                self.stdout.write(f'Filtrando por produto: {sku}')
            except Produto.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Produto com SKU "{sku}" não encontrado'))
                return

        if canal_nome:
            try:
                canal = CanalVenda.objects.get(nome=canal_nome)
                precos = precos.filter(canal=canal)
                self.stdout.write(f'Filtrando por canal: {canal_nome}')
            except CanalVenda.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Canal "{canal_nome}" não encontrado'))
                return

        total = precos.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('Nenhum preço encontrado para recalcular'))
            return

        self.stdout.write(f'Total de preços a recalcular: {total}')

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo dry-run: nenhuma alteração será feita'))
            for preco in precos.select_related('produto', 'canal')[:10]:
                self.stdout.write(f'  - {preco.produto.sku} / {preco.canal.nome}')
            if total > 10:
                self.stdout.write(f'  ... e mais {total - 10} preços')
            return

        salvar_historico = not sem_historico
        motivo = 'Recálculo em lote via comando'

        self.stdout.write('Iniciando recálculo...')

        recalculados = 0
        erros = 0

        for preco in precos.select_related('produto', 'canal'):
            try:
                with transaction.atomic():
                    preco.recalcular_precos(
                        salvar_historico=salvar_historico,
                        motivo=motivo
                    )
                recalculados += 1

                if recalculados % 100 == 0:
                    self.stdout.write(f'  Processados: {recalculados}/{total}')

            except Exception as e:
                erros += 1
                self.stderr.write(
                    self.style.ERROR(
                        f'Erro ao recalcular {preco.produto.sku}/{preco.canal.nome}: {e}'
                    )
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Recálculo concluído!'))
        self.stdout.write(f'  - Recalculados: {recalculados}')
        if erros:
            self.stdout.write(self.style.ERROR(f'  - Erros: {erros}'))
        if not salvar_historico:
            self.stdout.write(self.style.WARNING('  - Histórico NÃO foi salvo'))
