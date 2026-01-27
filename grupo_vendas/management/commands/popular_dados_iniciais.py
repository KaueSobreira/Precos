from django.core.management.base import BaseCommand
from grupo_vendas.models import GrupoCanais
from canais_vendas.models import CanalVenda


class Command(BaseCommand):
    help = 'Popula os dados iniciais e configura as estratégias de custo por grupo'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando carga de dados e configurações de custo...\n')

        # 1. Definição da Estrutura de Grupos e Canais
        estrutura_grupos = {
            'CasaMetais': {
                'is_default': True,
                'canais': [
                    'ML Clássico', 'ML Premium', 'TikTok', 'Temu', 'ML Clássico SN',
                    'Magalu', 'SHEIN', 'Shopee 20%', 'Shopee 14%', 'ML Premium SN',
                    'Amazon', 'Amazon Vendor', 'Carrefour/Casa&Vídeo', 'Shopee SN 20%',
                    'Leroy', 'Madeiramadeira', 'Olist', 'Via Varejo', 'Webcontinental',
                    'Tray', 'Tray S3G', 'SteelDecor', 'Afiliados', 'Tray MetalCromo',
                    'Mc Representante', 'Mc Repre. Online', 'Mc Repr. Pronta Entrega'
                ]
            },
            'S3G': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium', 'Carrefour', 'B2W', 'Via Varejo', 'Tray', 'Leroy Merlin', 'Madeiramadeira', 'Magalu', 'Shopee 14%', 'Shopee 20%', 'SHEIN']},
            'PontoDecor': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium', 'B2W', 'Madeiramadeira']},
            'CromoShop': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium', 'Madeiramadeira', 'Magalu', 'B2W', 'Shopee 14%', 'Shopee 20%', 'Via Varejo']},
            'Grupo Ghiz': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium', 'Shopee 14%', 'Shopee 20%', 'Amazon', 'Magalu']},
            'HomeFull': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium', 'Amazon', 'Via Varejo', 'B2W', 'Madeiramadeira', 'Magalu', 'Shopee 14%', 'Shopee 20%']},
            'CasaMoveis': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium', 'B2W', 'Shopee 14%', 'Shopee 20%', 'Magalu']},
            'ContelStore': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium', 'Shopee 14%', 'Shopee 20%', 'Magalu']},
            'SteelDecor Matriz': {'is_default': False, 'canais': ['ML Premium', 'ML Clássico', 'Shopee 14%', 'Shopee 20%', 'Magalu']},
            'SteelDecor SP': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium']},
            'SteelDecor PR': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium']},
            'SteelDecor BA': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium']},
            'Metallari': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium', 'Shopee 14%', 'Shopee 20%']},
            'Favolli': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium', 'Shopee 14%', 'Shopee 20%']},
            'BQHome': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium', 'Shopee 14%', 'Shopee 20%', 'Magalu']},
            'Birirp': {'is_default': False, 'canais': ['ML Clássico', 'ML Premium', 'Shopee 14%', 'Shopee 20%']},
        }

        # 2. Criar Grupos e Canais
        for nome_grupo, dados in estrutura_grupos.items():
            grupo, _ = GrupoCanais.objects.get_or_create(
                nome=nome_grupo,
                defaults={'is_default': dados['is_default']}
            )
            for nome_canal in dados['canais']:
                CanalVenda.objects.get_or_create(nome=nome_canal, grupo=grupo)

        # 3. Configurar Estratégias de Custo
        self.stdout.write('\nConfigurando estratégias de custo...')

        # Referências
        grupo_casa_metais = GrupoCanais.objects.get(nome='CasaMetais')
        canal_steel_ref = CanalVenda.objects.get(nome='SteelDecor', grupo=grupo_casa_metais)
        canal_afiliado_ref = CanalVenda.objects.get(nome='Afiliados', grupo=grupo_casa_metais)

        # Lista de Grupos que usam SteelDecor (CasaMetais) como custo
        grupos_ref_steel = [
            'SteelDecor Matriz', 'SteelDecor SP', 'SteelDecor PR', 
            'SteelDecor BA', 'Metallari'
        ]
        
        # Lista de Grupos que usam Afiliados (CasaMetais) como custo
        grupos_ref_afiliados = ['ContelStore']

        # Lista de Grupos que usam Custo do Produto (Padrão)
        grupos_padrao = [
            'CasaMetais', 'S3G', 'PontoDecor', 'CromoShop', 'Grupo Ghiz', 
            'HomeFull', 'CasaMoveis', 'Favolli', 'BQHome', 'Birirp'
        ]

        # Aplicar configurações
        for g_nome in grupos_ref_steel:
            GrupoCanais.objects.filter(nome=g_nome).update(
                tipo_custo='canal', canal_referencia_custo=canal_steel_ref
            )
            self.stdout.write(f'  - {g_nome}: Configurado para seguir SteelDecor (CasaMetais)')

        for g_nome in grupos_ref_afiliados:
            GrupoCanais.objects.filter(nome=g_nome).update(
                tipo_custo='canal', canal_referencia_custo=canal_afiliado_ref
            )
            self.stdout.write(f'  - {g_nome}: Configurado para seguir Afiliados (CasaMetais)')

        for g_nome in grupos_padrao:
            GrupoCanais.objects.filter(nome=g_nome).update(
                tipo_custo='padrao', canal_referencia_custo=None
            )
            self.stdout.write(f'  - {g_nome}: Configurado para Custo Padrão')

        self.stdout.write(self.style.SUCCESS('\nConfigurações concluídas com sucesso!'))