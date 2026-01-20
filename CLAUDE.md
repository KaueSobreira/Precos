# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Corporate pricing system (Sistema de Precificação) built with Django. Replaces Excel spreadsheets for managing product prices across multiple sales channels (marketplaces). Core principle: **"No price can be overwritten without being historized."**

## Commands

```bash
# Development server (uses SQLite by default)
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Populate initial data (groups and channels from PRD)
python manage.py popular_dados_iniciais

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Run tests for specific app
python manage.py test produtos
python manage.py test canais_vendas
python manage.py test grupo_vendas
```

## Architecture

### Django Apps

- **`produtos/`** - Products, BOM (Ficha Técnica), pricing per channel, price history
- **`canais_vendas/`** - Sales channels, freight tables, conditional freight rules
- **`grupo_vendas/`** - Channel groups (ecosystems) with inherited parameters

### Key Models and Relationships

```
GrupoCanais (grupo_vendas)
    └── CanalVenda (canais_vendas) - inherits percentage parameters
            └── PrecoProdutoCanal (produtos) - product price per channel
                    └── HistoricoPreco (produtos) - immutable price snapshots

Produto (produtos)
    └── ItemFichaTecnica - BOM items (MP/TR/EM types with multiplier)

TabelaFrete (canais_vendas)
    └── RegraFrete - conditional rules (IF/ELSE IF/ELSE)
```

### Pricing Formulas

All markups use the pattern: `100 * (1 / (100 - sum_of_percentages))`

- **Markup Frete**: `100 / (100 - (imposto + ads + comissao))`
- **Markup Venda**: `100 / (100 - (imposto + operacao + lucro + ads + comissao))`
- **Markup Promoção**: `100 / (100 - (imposto + operacao + promocao + ads + comissao))`
- **Markup Mínimo**: `100 / (100 - (imposto + operacao + minimo + ads + comissao))`

**Price calculation**: `preco = (markup_frete * frete) + (custo * markup_especifico)`

**Product weight**: `max(peso_fisico, peso_cubico)` where `peso_cubico = (L * A * P) / 6000`

### Critical Business Rules

1. **Price History**: Any change affecting price MUST trigger `salvar_historico()` before saving
2. **HistoricoPreco is immutable**: `save()` blocks updates, `delete()` raises ValidationError
3. **ECOSSISTEMA group** (`is_default=True`) cannot be deleted
4. **Validation**: `promocao >= minimo`, sum of percentages < 100%
5. **Channels inherit from groups** unless `herdar_grupo=False`

### Localization

Brazilian Portuguese (`pt-br`), timezone `America/Sao_Paulo`. Decimal separator is comma, thousand separator is period.
