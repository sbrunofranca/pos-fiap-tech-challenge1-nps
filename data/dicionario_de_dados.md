# Dicionário de dados — `desafio_nps_fase_1.csv`

Unidade de análise: **1 linha = 1 pedido** respondido na pesquisa de NPS. Total: 2.500 linhas, 19 colunas, sem valores nulos.

| Coluna | Tipo | Faixa observada | Descrição | Uso no modelo |
|---|---|---|---|---|
| `customer_id` | inteiro | 1 – 2.500 | Identificador do cliente | Fora (identificador) |
| `customer_age` | inteiro | 18 – 69 | Idade do cliente (anos) | Entra |
| `customer_region` | categórica | Norte, Nordeste, Centro-Oeste, Sudeste, Sul | Região do cliente | Entra (dummies) |
| `customer_tenure_months` | inteiro | 1 – 119 | Tempo de relacionamento com a empresa (meses) | Entra |
| `order_id` | inteiro | 50.001 – 52.500 | Identificador do pedido | Fora (identificador) |
| `order_value` | decimal | R$ 7,76 – R$ 1.983,81 | Valor do pedido | Entra |
| `items_quantity` | inteiro | 1 – 6 | Quantidade de itens no pedido | Entra |
| `discount_value` | decimal | R$ 0,02 – R$ 230,33 | Valor do desconto concedido | Entra |
| `payment_installments` | inteiro | 1 – 11 | Número de parcelas | Entra |
| `freight_value` | decimal | R$ 2,62 – R$ 76,13 | Valor do frete | Entra |
| `delivery_time_days` | inteiro | 2 – 14 | Prazo total de entrega (dias) | Entra |
| `delivery_delay_days` | inteiro | 0 – 8 | Dias de atraso em relação ao prazo prometido | Entra |
| `delivery_attempts` | inteiro | 1 – 3 | Tentativas de entrega | Entra |
| `customer_service_contacts` | inteiro | 0 – 7 | Contatos do cliente com o SAC | Entra (cenário B) |
| `complaints_count` | inteiro | 0 – 11 | Reclamações registradas | Entra (cenário B) |
| `resolution_time_days` | inteiro | 0 – 11 | Tempo de resolução do atendimento (dias) | Entra (cenário B) |
| `nps_score` | decimal | 0 – 10 | Nota de NPS ("quanto recomendaria a empresa") | **Origem da target** |
| `repeat_purchase_30d` | binária | 0 / 1 | Recompra nos 30 dias seguintes | Fora (vazamento: posterior e derivada da nota) |
| `csat_internal_score` | decimal | 0 – 10 | Satisfação interna (CSAT) | Fora (outra medida de satisfação) |

## Variáveis derivadas

| Variável | Regra | Uso |
|---|---|---|
| `categoria_nps` | Detrator (0 a 6), Neutro (7 a 8), Promotor (9 a 10) | Cálculo do NPS e análises |
| `detrator` | 1 se `nps_score` < 7; 0 caso contrário | **Variável-alvo do modelo** |

## Pontos de atenção de qualidade
- `nps_score` e `csat_internal_score` têm casas decimais, o que não acontece em uma pesquisa real de NPS.
- `repeat_purchase_30d` é 0 para toda nota abaixo de 8 e 1 a partir de 8: foi calculada a partir da nota.
- Não há datas: não é possível confirmar se reclamações e contatos ocorreram antes da pesquisa.
