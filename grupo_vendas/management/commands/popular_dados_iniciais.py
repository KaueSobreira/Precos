from django.core.management.base import BaseCommand
from grupo_vendas.models import GrupoCanais
from canais_vendas.models import CanalVenda


class Command(BaseCommand):
    help = 'Popula os dados iniciais do sistema (Grupo ECOSSISTEMA e canais padrão)'

    def handle(self, *args, **options):
        self.stdout.write('Criando dados iniciais...\n')

        # Criar grupo ECOSSISTEMA (padrão)
        ecossistema, created = GrupoCanais.objects.get_or_create(
            nome='ECOSSISTEMA',
            defaults={
                'descricao': 'Grupo padrão contendo todos os marketplaces e canais de venda',
                'is_default': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo ECOSSISTEMA criado'))
        else:
            self.stdout.write('Grupo ECOSSISTEMA já existe')

        # Lista de canais do grupo ECOSSISTEMA (conforme PRD)
        canais_ecossistema = [
            'ML Clássico',
            'ML Premium',
            'TikTok',
            'Temu',
            'B2W',
            'Magalu',
            'SHEIN',
            'Shopee 20%',
            'Shopee 14%',
            'Aliexpress',
            'Amazon',
            'Amazon Vendor',
            'Carrefour / Casa & Vídeo',
            'Colombo',
            'Leroy',
            'Madeiramadeira',
            'Olist',
            'Via Varejo',
            'Webcontinental',
            'Tray',
            'Tray S3G',
            'SteelDecor',
            'Afiliados',
            'Tray MetalCromo',
            'Mc Representante',
            'Mc Repre. Online',
            'Mc Repr. Pronta Entrega',
        ]

        for nome_canal in canais_ecossistema:
            canal, created = CanalVenda.objects.get_or_create(
                nome=nome_canal,
                grupo=ecossistema,
                defaults={'herdar_grupo': True}
            )
            if created:
                self.stdout.write(f'  Canal "{nome_canal}" criado')

        self.stdout.write('')

        # Criar grupos específicos
        grupos_especificos = {
            'STEEL': [
                'ML Clássico Steel',
                'ML Premium Steel',
                'Shopee 14% Steel',
                'Magalu Steel',
            ],
            'CONTEL': [
                'ML Clássico Contel',
                'ML Premium Contel',
                'Shopee 14% Contel',
                'Magalu Contel',
            ],
            'METALLARI': [
                'ML Clássico Metallari',
                'ML Premium Metallari',
                'Shopee 14% Metallari',
                'Magalu Metallari',
            ],
        }

        for nome_grupo, canais in grupos_especificos.items():
            grupo, created = GrupoCanais.objects.get_or_create(
                nome=nome_grupo,
                defaults={
                    'descricao': f'Grupo específico {nome_grupo}',
                    'is_default': False,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo {nome_grupo} criado'))
            else:
                self.stdout.write(f'Grupo {nome_grupo} já existe')

            for nome_canal in canais:
                canal, created = CanalVenda.objects.get_or_create(
                    nome=nome_canal,
                    grupo=grupo,
                    defaults={'herdar_grupo': True}
                )
                if created:
                    self.stdout.write(f'  Canal "{nome_canal}" criado')

            self.stdout.write('')

        self.stdout.write(self.style.SUCCESS('\nDados iniciais criados com sucesso!'))

        # Resumo
        total_grupos = GrupoCanais.objects.count()
        total_canais = CanalVenda.objects.count()
        self.stdout.write(f'\nResumo:')
        self.stdout.write(f'  - Total de grupos: {total_grupos}')
        self.stdout.write(f'  - Total de canais: {total_canais}')
