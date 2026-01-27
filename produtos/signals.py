"""
Signals para recálculo automático de preços.

Dispara recálculo quando:
- TabelaFrete ou suas regras são alteradas
- TabelaTaxa ou suas regras são alteradas
- CanalVenda é alterado
- GrupoCanais é alterado (afeta canais que herdam)
- Produto tem dimensões/peso alterados
- ItemFichaTecnica é alterado (afeta custo)
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction


def recalcular_precos_canal(canal, motivo):
    """Recalcula todos os preços de um canal específico."""
    from .models import PrecoProdutoCanal

    precos = PrecoProdutoCanal.objects.filter(canal=canal, ativo=True)
    for preco in precos:
        preco.recalcular_precos(salvar_historico=True, motivo=motivo)

    return precos.count()


def recalcular_precos_produto(produto, motivo):
    """Recalcula todos os preços de um produto específico."""
    from .models import PrecoProdutoCanal

    precos = PrecoProdutoCanal.objects.filter(produto=produto, ativo=True)
    for preco in precos:
        preco.recalcular_precos(salvar_historico=True, motivo=motivo)

    return precos.count()


def recalcular_precos_tabela_frete(tabela_frete, motivo):
    """Recalcula todos os preços de canais que usam uma tabela de frete."""
    from canais_vendas.models import CanalVenda
    from .models import PrecoProdutoCanal

    canais = CanalVenda.objects.filter(tabela_frete=tabela_frete)
    total = 0

    for canal in canais:
        precos = PrecoProdutoCanal.objects.filter(canal=canal, ativo=True)
        for preco in precos:
            preco.recalcular_precos(salvar_historico=True, motivo=motivo)
        total += precos.count()

    return total


def recalcular_precos_tabela_taxa(tabela_taxa, motivo):
    """Recalcula todos os preços de canais que usam uma tabela de taxa."""
    from canais_vendas.models import CanalVenda
    from .models import PrecoProdutoCanal

    canais = CanalVenda.objects.filter(tabela_taxa=tabela_taxa)
    total = 0

    for canal in canais:
        precos = PrecoProdutoCanal.objects.filter(canal=canal, ativo=True)
        for preco in precos:
            preco.recalcular_precos(salvar_historico=True, motivo=motivo)
        total += precos.count()

    return total


def recalcular_precos_grupo(grupo, motivo):
    """Recalcula todos os preços de canais de um grupo."""
    from canais_vendas.models import CanalVenda
    from .models import PrecoProdutoCanal

    # Recalcula todos os canais do grupo, pois configurações como "Tipo de Custo"
    # afetam a todos, independente da flag 'herdar_grupo'
    canais = CanalVenda.objects.filter(grupo=grupo)
    total = 0

    for canal in canais:
        precos = PrecoProdutoCanal.objects.filter(canal=canal, ativo=True)
        for preco in precos:
            preco.recalcular_precos(salvar_historico=True, motivo=motivo)
        total += precos.count()

    return total


# ============================================================
# SIGNALS PARA TABELA DE FRETE
# ============================================================

@receiver(post_save, sender='tabela_frete.TabelaFrete')
def on_tabela_frete_save(sender, instance, **kwargs):
    """Quando uma tabela de frete é alterada, recalcula preços dos canais que a usam."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_frete(
            instance,
            f'Tabela de frete "{instance.nome}" atualizada'
        )
    )


@receiver(post_save, sender='tabela_frete.RegraFreteMatriz')
def on_regra_matriz_save(sender, instance, **kwargs):
    """Quando uma regra de matriz é alterada."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_frete(
            instance.tabela,
            f'Regra de frete (matriz) atualizada na tabela "{instance.tabela.nome}"'
        )
    )


@receiver(post_delete, sender='tabela_frete.RegraFreteMatriz')
def on_regra_matriz_delete(sender, instance, **kwargs):
    """Quando uma regra de matriz é excluída."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_frete(
            instance.tabela,
            f'Regra de frete (matriz) excluída da tabela "{instance.tabela.nome}"'
        )
    )


@receiver(post_save, sender='tabela_frete.RegraFreteSimples')
def on_regra_simples_save(sender, instance, **kwargs):
    """Quando uma regra simples é alterada."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_frete(
            instance.tabela,
            f'Regra de frete (simples) atualizada na tabela "{instance.tabela.nome}"'
        )
    )


@receiver(post_delete, sender='tabela_frete.RegraFreteSimples')
def on_regra_simples_delete(sender, instance, **kwargs):
    """Quando uma regra simples é excluída."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_frete(
            instance.tabela,
            f'Regra de frete (simples) excluída da tabela "{instance.tabela.nome}"'
        )
    )


@receiver(post_save, sender='tabela_frete.RegraFreteEspecial')
def on_regra_especial_save(sender, instance, **kwargs):
    """Quando uma regra especial e alterada."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_frete(
            instance.tabela,
            f'Regra especial de frete atualizada na tabela "{instance.tabela.nome}"'
        )
    )


@receiver(post_delete, sender='tabela_frete.RegraFreteEspecial')
def on_regra_especial_delete(sender, instance, **kwargs):
    """Quando uma regra especial e excluida."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_frete(
            instance.tabela,
            f'Regra especial de frete excluida da tabela "{instance.tabela.nome}"'
        )
    )


@receiver(post_save, sender='tabela_frete.DescontoNotaVendedor')
def on_desconto_nota_save(sender, instance, **kwargs):
    """Quando um desconto por nota é alterado."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_frete(
            instance.tabela,
            f'Desconto por nota atualizado na tabela "{instance.tabela.nome}"'
        )
    )


@receiver(post_delete, sender='tabela_frete.DescontoNotaVendedor')
def on_desconto_nota_delete(sender, instance, **kwargs):
    """Quando um desconto por nota é excluído."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_frete(
            instance.tabela,
            f'Desconto por nota excluído da tabela "{instance.tabela.nome}"'
        )
    )


# ============================================================
# SIGNALS PARA TABELA DE TAXA
# ============================================================

@receiver(post_save, sender='tabela_frete.TabelaTaxa')
def on_tabela_taxa_save(sender, instance, **kwargs):
    """Quando uma tabela de taxa é alterada."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_taxa(
            instance,
            f'Tabela de taxa "{instance.nome}" atualizada'
        )
    )


@receiver(post_save, sender='tabela_frete.RegraTaxa')
def on_regra_taxa_save(sender, instance, **kwargs):
    """Quando uma regra de taxa é alterada."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_taxa(
            instance.tabela,
            f'Regra de taxa atualizada na tabela "{instance.tabela.nome}"'
        )
    )


@receiver(post_delete, sender='tabela_frete.RegraTaxa')
def on_regra_taxa_delete(sender, instance, **kwargs):
    """Quando uma regra de taxa é excluída."""
    transaction.on_commit(
        lambda: recalcular_precos_tabela_taxa(
            instance.tabela,
            f'Regra de taxa excluída da tabela "{instance.tabela.nome}"'
        )
    )


# ============================================================
# SIGNALS PARA CANAL DE VENDA
# ============================================================

@receiver(post_save, sender='canais_vendas.CanalVenda')
def on_canal_venda_save(sender, instance, **kwargs):
    """Quando um canal de venda é alterado, recalcula todos os seus preços."""
    transaction.on_commit(
        lambda: recalcular_precos_canal(
            instance,
            f'Canal de venda "{instance.nome}" atualizado'
        )
    )


# ============================================================
# SIGNALS PARA GRUPO DE CANAIS
# ============================================================

@receiver(post_save, sender='grupo_vendas.GrupoCanais')
def on_grupo_canais_save(sender, instance, **kwargs):
    """Quando um grupo é alterado, recalcula preços dos canais que herdam."""
    transaction.on_commit(
        lambda: recalcular_precos_grupo(
            instance,
            f'Grupo de canais "{instance.nome}" atualizado'
        )
    )


# ============================================================
# SIGNALS PARA PRODUTO
# ============================================================

@receiver(post_save, sender='produtos.Produto')
def on_produto_save(sender, instance, **kwargs):
    """Quando um produto é alterado (peso, dimensões), recalcula seus preços."""
    transaction.on_commit(
        lambda: recalcular_precos_produto(
            instance,
            f'Produto "{instance.sku}" atualizado'
        )
    )


# ============================================================
# SIGNALS PARA FICHA TÉCNICA (CUSTO)
# ============================================================

@receiver(post_save, sender='produtos.ItemFichaTecnica')
def on_item_ficha_save(sender, instance, **kwargs):
    """Quando um item da ficha técnica é alterado, recalcula preços do produto."""
    transaction.on_commit(
        lambda: recalcular_precos_produto(
            instance.produto,
            f'Ficha técnica do produto "{instance.produto.sku}" atualizada'
        )
    )


@receiver(post_delete, sender='produtos.ItemFichaTecnica')
def on_item_ficha_delete(sender, instance, **kwargs):
    """Quando um item da ficha técnica é excluído."""
    transaction.on_commit(
        lambda: recalcular_precos_produto(
            instance.produto,
            f'Item excluído da ficha técnica do produto "{instance.produto.sku}"'
        )
    )


# ============================================================
# SIGNALS PARA PREÇO PRODUTO (CADEIA DE REFERÊNCIA)
# ============================================================

@receiver(post_save, sender='produtos.PrecoProdutoCanal')
def on_preco_save(sender, instance, **kwargs):
    """
    Quando um preço é atualizado, verifica se este canal serve de referência
    de custo para outros grupos. Se sim, dispara o recálculo desses grupos.
    """
    if kwargs.get('raw', False):
        return

    # Evita loop: se o save foi disparado por um recálculo, não propaga
    # (Embora a lógica de recálculo já proteja, é bom evitar)
    # Mas aqui é difícil saber se foi recálculo. O loop infinito é evitado
    # pela verificação de valores no metodo _calcular_preco_iterativo
    # e pelo fato de que a referência é unidirecional (Grupo -> Canal).
    # Se houver referência circular (Grupo A usa Canal B, Grupo B usa Canal A),
    # aí teremos problemas, mas o usuário deve evitar isso.

    from grupo_vendas.models import GrupoCanais

    # Busca grupos que usam este canal como referência
    grupos_afetados = GrupoCanais.objects.filter(
        tipo_custo='canal',
        canal_referencia_custo=instance.canal
    )

    if grupos_afetados.exists():
        def disparar_recalculo_grupos():
            for grupo in grupos_afetados:
                # Otimização: Recalcular apenas o produto específico no grupo
                # em vez do grupo todo.
                # Mas a função recalcular_precos_grupo faz tudo.
                # Vamos criar uma lógica local aqui para ser mais eficiente.
                from canais_vendas.models import CanalVenda
                from .models import PrecoProdutoCanal as PrecoModel

                canais_grupo = CanalVenda.objects.filter(grupo=grupo)
                for canal in canais_grupo:
                    # Busca o preço deste mesmo produto no canal do grupo
                    preco_filho = PrecoModel.objects.filter(
                        canal=canal,
                        produto=instance.produto, # Mesmíssimo produto
                        ativo=True
                    ).first()
                    
                    if preco_filho:
                        preco_filho.recalcular_precos(
                            salvar_historico=True, 
                            motivo=f'Preço base alterado no canal referência "{instance.canal.nome}"'
                        )

        transaction.on_commit(disparar_recalculo_grupos)
