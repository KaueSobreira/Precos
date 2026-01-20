# Sistema de Precificação Corporativo

Sistema Django para gerenciamento de preços de produtos em múltiplos canais de venda (marketplaces). Substitui planilhas Excel com regra fundamental: **"Nenhum preço pode ser sobrescrito sem ser historizado."**

## Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Modelos e Relacionamentos](#modelos-e-relacionamentos)
- [Cálculos de Precificação](#cálculos-de-precificação)
- [Sistema de Frete](#sistema-de-frete)
- [Histórico de Preços](#histórico-de-preços)
- [Instalação e Comandos](#instalação-e-comandos)
- [Regras de Negócio](#regras-de-negócio)

---

## Visão Geral

O sistema permite:
- Gerenciar produtos com Ficha Técnica (BOM - Bill of Materials)
- Configurar canais de venda com parâmetros específicos (impostos, comissões, etc.)
- Calcular preços automaticamente baseado em markups
- Manter histórico completo de alterações de preços
- Configurar tabelas de frete complexas (por peso, preço ou matriz 2D)

### Stack Tecnológico
- **Backend:** Django 6.0.1
- **Banco de Dados:** SQLite (dev) / PostgreSQL (prod)
- **Precisão Financeira:** Python Decimal
- **Localização:** Português Brasil (pt-br), Timezone America/Sao_Paulo

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        GRUPO DE CANAIS                          │
│  (Ecossistema: Mercado Livre, Amazon, Shopee, etc.)            │
│  Parâmetros: imposto, operação, lucro, promoção, mínimo,       │
│              ads, comissão                                      │
└─────────────────────┬───────────────────────────────────────────┘
                      │ herda parâmetros (se herdar_grupo=True)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CANAL DE VENDA                             │
│  (Ex: ML Full, ML Clássico, Amazon FBA, Shopee Express)        │
│  - Pode sobrescrever parâmetros do grupo                       │
│  - Define tipo de frete (fixo ou tabela)                       │
│  - Calcula markups automaticamente                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PREÇO PRODUTO CANAL                           │
│  Vincula: Produto ←→ Canal                                      │
│  - Modo automático: calcula baseado em custo + markups         │
│  - Modo manual: permite sobrescrever preços                    │
│  - Gera histórico a cada alteração                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HISTÓRICO DE PREÇOS                          │
│  Registro IMUTÁVEL de todas as alterações                       │
│  - Não pode ser editado nem excluído                           │
│  - Captura: custo, preços, frete, taxa, usuário, data, motivo  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Modelos e Relacionamentos

### Produto
```
Produto
├── sku (único)
├── titulo
├── ean
├── Dimensões: largura, altura, profundidade (cm)
├── peso_fisico (kg)
├── Propriedades calculadas:
│   ├── peso_cubico = (L × A × P) / 6000
│   ├── peso_produto = max(peso_fisico, peso_cubico)
│   └── custo = soma de todos itens da ficha técnica
└── Relacionamento: 1-N com ItemFichaTecnica
```

### Ficha Técnica (BOM)
```
ItemFichaTecnica
├── tipo: MP (Matéria Prima), TR (Terceirizado), EM (Embalagem)
├── codigo, descricao
├── unidade (UN, PC, KG, M, etc.)
├── quantidade
├── custo_unitario
├── multiplicador (default: 1.00)
└── custo_total = quantidade × custo_unitario × multiplicador
```

### Grupo de Canais
```
GrupoCanais
├── nome (único)
├── is_default (ECOSSISTEMA não pode ser excluído)
└── Parâmetros percentuais:
    ├── imposto (%)
    ├── operacao (%)
    ├── lucro (%)
    ├── promocao (%)
    ├── minimo (%)
    ├── ads (%)
    └── comissao (%)
```

### Canal de Venda
```
CanalVenda
├── nome
├── grupo (FK → GrupoCanais)
├── herdar_grupo (boolean)
├── tipo_frete: 'fixo' ou 'tabela'
├── frete_fixo (se tipo_frete='fixo')
├── tabela_frete (FK → TabelaFrete)
├── tabela_taxa (FK → TabelaTaxa)
├── nota_vendedor (1-5, para descontos de frete)
└── Parâmetros próprios (sobrescrevem grupo se herdar_grupo=False)
```

---

## Cálculos de Precificação

### Fórmula dos Markups

Todos os markups seguem o padrão:
```
Markup = 100 / (100 - soma_dos_percentuais)
```

#### Tipos de Markup

| Markup | Fórmula | Uso |
|--------|---------|-----|
| **Frete** | `100 / (100 - (imposto + ads + comissão))` | Aplicado sobre o frete |
| **Venda** | `100 / (100 - (imposto + operação + lucro + ads + comissão))` | Preço normal de venda |
| **Promoção** | `100 / (100 - (imposto + operação + promoção + ads + comissão))` | Preço promocional |
| **Mínimo** | `100 / (100 - (imposto + operação + mínimo + ads + comissão))` | Preço mínimo (margem mínima) |

### Fórmula do Preço

```
Preço = (Markup_Frete × Frete) + (Custo × Markup_Específico)
```

Onde:
- **Custo** = soma de todos os itens da ficha técnica
- **Frete** = obtido da tabela de frete (baseado em peso e/ou preço)
- **Markup_Específico** = markup_venda, markup_promocao ou markup_minimo

### Algoritmo Iterativo

Como o frete e taxa podem depender do preço (dependência circular), usamos um algoritmo iterativo:

```python
def calcular_preco(custo, canal, markup_target):
    preco = 0
    frete = 0
    taxa = 0

    for _ in range(10):  # máximo 10 iterações
        novo_preco = ((custo + taxa) × markup_target) + (frete × markup_frete)
        nova_taxa = obter_taxa(novo_preco)
        novo_frete = obter_frete(peso, novo_preco)

        if convergiu(novo_preco, nova_taxa, novo_frete):
            break

        preco, taxa, frete = novo_preco, nova_taxa, novo_frete

    return preco
```

### Exemplo de Cálculo

**Dados:**
- Produto: custo R$ 100,00, peso 2 kg
- Canal: imposto=10%, operação=5%, lucro=20%, ads=2%, comissão=3%
- Frete fixo: R$ 15,00

**Cálculo:**
```
1. Markup Venda = 100 / (100 - 40) = 1,6667
2. Markup Frete = 100 / (100 - 15) = 1,1765
3. Preço = (15 × 1,1765) + (100 × 1,6667)
        = 17,65 + 166,67
        = R$ 184,32
```

---

## Sistema de Frete

### Tipos de Tabela de Frete

| Tipo | Descrição | Parâmetros |
|------|-----------|------------|
| **Fixo** | Valor único para todos os produtos | `frete_fixo` no canal |
| **Peso** | Baseado no peso do produto | Faixas de peso |
| **Preço** | Baseado no preço de venda | Faixas de preço |
| **Matriz** | Combinação peso × preço | Grade 2D |

### Regras de Frete

**Regra Simples (peso ou preço):**
```
Se valor >= inicio E valor < fim:
    frete = valor_frete
```

**Regra Matriz (2D):**
```
Se peso >= peso_inicio E peso < peso_fim
   E preco >= preco_inicio E preco < preco_fim:
    frete = valor_frete
```

### Desconto por Nota do Vendedor

Vendedores com boa reputação (nota 1-5) podem ter descontos no frete:
```
frete_final = frete × (100 - percentual_desconto) / 100 + taxa_fixa
```

---

## Histórico de Preços

### Princípio de Imutabilidade

O modelo `HistoricoPreco` é **completamente imutável**:

```python
class HistoricoPreco(models.Model):
    def save(self):
        if self.pk:
            raise ValidationError("Histórico não pode ser alterado")
        super().save()

    def delete(self):
        raise ValidationError("Histórico não pode ser excluído")
```

### Dados Capturados

Cada registro de histórico contém:
- `produto`, `canal` (referências)
- `custo` (custo do produto no momento)
- `preco_venda`, `preco_promocao`, `preco_minimo`
- `frete_aplicado`, `taxa_extra`
- `data_registro` (timestamp automático)
- `usuario` (quem fez a alteração)
- `motivo` (justificativa da alteração)

### Quando é Gerado

O histórico é criado automaticamente:
```python
# PrecoProdutoCanal.save()
@transaction.atomic
def save(self, *args, **kwargs):
    if self.pk:  # apenas em updates
        self.salvar_historico()
    super().save(*args, **kwargs)
```

---

## Instalação e Comandos

### Requisitos
- Python 3.10+
- Django 6.0.1

### Instalação

```bash
# Clonar repositório
git clone <repo-url>
cd Precos

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Popular dados iniciais (grupos e canais do PRD)
python manage.py popular_dados_iniciais

# Criar superusuário
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

### Comandos Úteis

```bash
# Migrações
python manage.py makemigrations
python manage.py migrate

# Testes
python manage.py test
python manage.py test produtos
python manage.py test canais_vendas

# Shell Django
python manage.py shell
```

---

## Regras de Negócio

### Validações

| Regra | Descrição |
|-------|-----------|
| Soma < 100% | `imposto + operação + lucro + ads + comissão < 100` |
| Promoção ≥ Mínimo | Margem promocional não pode ser menor que a mínima |
| ECOSSISTEMA protegido | Grupo padrão não pode ser excluído |
| Tipo frete | Se `tipo_frete='tabela'`, deve selecionar tabela |

### Herança de Parâmetros

Canais herdam parâmetros do grupo quando:
- `herdar_grupo = True`, OU
- Campo específico é `None`

```python
def imposto_efetivo(self):
    if self.herdar_grupo or self.imposto is None:
        return self.grupo.imposto
    return self.imposto
```

### Peso do Produto

O peso usado para cálculo de frete é sempre o maior entre:
```python
peso_cubico = (largura × altura × profundidade) / 6000
peso_produto = max(peso_fisico, peso_cubico)
```

### Desconto Máximo

Calculado como a diferença percentual entre preço de venda e mínimo:
```python
desconto_maximo = ((preco_venda - preco_minimo) / preco_venda) × 100
```

---

## Estrutura de Diretórios

```
Precos/
├── app/                    # Configurações Django
│   ├── settings.py
│   └── urls.py
├── grupo_vendas/           # App: Grupos de canais
├── canais_vendas/          # App: Canais de venda
├── produtos/               # App: Produtos, BOM, Preços, Histórico
├── tabela_frete/           # App: Tabelas de frete e taxa
├── controle_producao/      # App: Componentes PCP
├── templates/              # Templates HTML
├── static/                 # Arquivos estáticos
├── manage.py
└── README.md
```

---

## Considerações de Performance

### Cálculos em Tempo Real

Atualmente, os preços são calculados como `@property` (em tempo real):
- `preco_venda`, `preco_promocao`, `preco_minimo`

**Vantagem:** Sempre reflete dados atualizados
**Desvantagem:** Pode ficar lento com muitos produtos/canais

### Recomendações para Escala

Para grandes volumes, considere:

1. **Cache de Preços:** Salvar preços calculados no banco
2. **Atualização em Lote:** Recalcular via comando/task assíncrona
3. **Cache Redis:** Para consultas frequentes
4. **Índices:** Garantir índices em campos de busca (sku, canal)

---

## Licença

Projeto interno - uso corporativo.
