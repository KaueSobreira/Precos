# PRD – Sistema Corporativo de Precificação por Markup, Frete Condicional e Ecossistema de Marketplaces

## 1. Objetivo

Desenvolver um sistema corporativo de **formação e controle de preços**, substituindo planilhas Excel, mantendo **exatamente a lógica atual de cálculo**, com:

- Margem protegida
- Preço mínimo obrigatório
- Padronização por grupos (ecossistemas)
- Histórico completo de preços
- Frete fixo ou calculado por regras condicionais

O sistema deve **impedir erro humano** e respeitar práticas tradicionais de precificação.

---

## 2. Princípio Fundamental (Regra de Ouro)

> **Nenhum preço pode ser sobrescrito sem ser historizado.**

Qualquer alteração que impacte preço deve obrigatoriamente:

1. Salvar o estado atual no histórico
2. Aplicar a alteração
3. Recalcular todos os valores
4. Gerar nova versão ativa

---

## 3. Escopo

### Inclui

- Cadastro de produtos
- Cálculo de peso físico e cúbico
- Ficha técnica e custo
- Precificação por canal de venda
- Grupos de canais (ecossistemas)
- Markups automáticos
- Frete fixo ou por tabela condicional
- Edição em massa
- Simulação de impacto
- Histórico/versionamento de preços
- Auditoria completa

### Não inclui (fase inicial)

- Publicação automática em marketplaces
- Integração contábil
- Controle de estoque

---

## 4. Perfil de Usuário

- Analista comercial
- Gestor de preços

Usuário **não é técnico**.  
O sistema protege o negócio, não ensina matemática.

---

## 5. Cadastro de Produto

### 5.1 Campos do Produto

Campos cadastrados no **nível do produto**, independentes de marketplace:

| Campo               | Tipo           | Regra                                                     |
| ------------------- | -------------- | --------------------------------------------------------- |
| Título Principal    | Texto          | Obrigatório                                               |
| SKU                 | Texto          | Obrigatório                                               |
| EAN                 | Texto          | Opcional                                                  |
| Largura             | Numérico (cm)  | Obrigatório                                               |
| Altura              | Numérico (cm)  | Obrigatório                                               |
| Profundidade        | Numérico (cm)  | Obrigatório                                               |
| Peso Físico         | Numérico (kg)  | Digitado                                                  |
| Peso Cúbico         | Calculado      | `(L * A * P) / 6000`                                      |
| Peso Produto        | Calculado      | `SE(Peso Físico > Peso Cúbico; Peso Físico; Peso Cúbico)` |
| Títulos Secundários | Lista de texto | Opcional                                                  |

👉 **Peso Produto** é o peso final usado para cálculo de frete.

---

## 6. Ficha Técnica do Produto (Kit)

Cada produto pode ser um **kit**.

Campos:

- Código do item
- Descrição
- Quantidade por kit
- Custo unitário
- Custo total do item

O **custo do produto** é a soma automática da ficha técnica.

---

## 7. Grupos de Canais (Ecossistemas)

Todo canal pertence obrigatoriamente a **1 grupo**.

### 7.1 Grupo Padrão – ECOSSISTEMA (imutável)

- ML Clássico
- ML Premium
- TikTok
- Temu
- B2W
- Magalu
- SHEIN
- Shopee 20%
- Shopee 14%
- Aliexpress
- Amazon
- Amazon Vendor
- Carrefour / Casa & Vídeo
- Colombo
- Leroy
- Madeiramadeira
- Olist
- Via Varejo
- Webcontinental
- Tray
- Tray S3G
- SteelDecor
- Afiliados
- Tray MetalCromo
- Mc Representante
- Mc Repre. Online
- Mc Repr. Pronta Entrega

---

### 7.2 Grupos Específicos

**STEEL**

- ML Clássico Steel
- ML Premium Steel
- Shopee 14% Steel
- Magalu Steel

**CONTEL**

- ML Clássico Contel
- ML Premium Contel
- Shopee 14% Contel
- Magalu Contel

**METALLARI**

- ML Clássico Metallari
- ML Premium Metallari
- Shopee 14% Metallari
- Magalu Metallari

---

## 8. Cadastro de Canal de Venda

Cada canal **repete os mesmos campos e fórmulas**.

### 8.1 Campos Digitados (Input)

- imposto (%)
- operação (%)
- lucro (%)
- promoção (%)
- mínimo (%)
- ads (%)
- comissão (%)
- taxa / frete (fixo ou tabela)

---

## 9. Markups (Campos Calculados)

### Markup Frete

markup_frete = 100 \* (1 / (100 - (imposto + ads + comissao)))

shell
Copiar código

### Markup Venda

markup_venda = 100 \* (1 / (100 - (imposto + operacao + lucro + ads + comissao)))

shell
Copiar código

### Markup Promoção

markup_promocao = 100 \* (1 / (100 - (imposto + operacao + promocao + ads + comissao)))

shell
Copiar código

### Markup Mínimo

markup_minimo = 100 \* (1 / (100 - (imposto + operacao + minimo + ads + comissao)))

yaml
Copiar código

---

## 10. Cálculo de Preços

preco =
(markup_frete \* frete)

(custo \* markup_especifico)

yaml
Copiar código

Aplicável para:

- Preço de venda
- Preço promocional
- Preço mínimo

---

## 11. Desconto Máximo Permitido

% desconto até =
((preco_venda - preco_minimo) / preco_venda) \* 100

yaml
Copiar código

Campo somente leitura.

---

## 12. Frete

### 12.1 Frete Fixo

- Valor digitado manualmente no canal

---

### 12.2 Frete por Tabela Condicional (Requisito Crítico)

O sistema deve permitir cadastrar **tabelas de frete reutilizáveis**.

#### Estrutura da Tabela

- Nome
- Tipo:
  - Por peso (usa Peso Produto)
  - Por preço (usa Preço de Venda)

#### Regras Condicionais (Interface)

- SE
- SENÃO SE
- SENÃO (obrigatório)

Exemplo:

- SE peso ≤ 1 kg → frete = X
- SENÃO SE peso ≤ 5 kg → frete = Y
- SENÃO → frete = Z

No canal, o usuário escolhe:

- frete fixo
- ou tabela de frete

---

## 13. Herança e Edição em Massa

- Grupos definem valores padrão
- Canais herdam automaticamente
- Campos podem ser sobrescritos
- Alterações no grupo propagam para todos os canais
- Sempre com histórico antes do recalculo

---

## 14. Versionamento e Histórico de Preços

### 14.1 Quando versionar

Sempre que mudar:

- qualquer percentual
- custo
- frete ou tabela de frete
- grupo ou canal

---

### 14.2 Conteúdo do Histórico

Cada versão salva:

- Produto
- Canal
- Grupo
- Todos os parâmetros (%)
- Frete aplicado
- Markups
- Preço venda / promoção / mínimo
- Usuário
- Data/hora
- Motivo (opcional)

Histórico é **imutável**.

---

## 15. Regras Invioláveis

1. Promoção ≥ mínimo
2. Percentuais somados < 100
3. Frete nunca entra no custo
4. Nenhum preço é perdido
5. Grupo ECOSSISTEMA não pode ser removido

---

## 16. Critério de Aceite

O sistema será aceito se:

- Reproduzir 100% o Excel atual
- Permitir frete fixo ou condicional
- Permitir edição em massa
- Manter histórico completo
- Bloquear qualquer quebra de margem

---

## 17. Visão Final

Este sistema **não é um precificador genérico**.

É um **motor corporativo de margem com memória**:

> custo → peso → frete → markup → preço  
> preço muda → histórico fica  
> margem nunca quebra
