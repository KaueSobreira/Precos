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
    """Recalcula todos os preços de canais de um grupo (que herdam do grupo)."""
    from canais_vendas.models import CanalVenda
    from .models import PrecoProdutoCanal

    # Apenas canais que herdam do grupo
    canais = CanalVenda.objects.filter(grupo=grupo, herdar_grupo=True)
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
