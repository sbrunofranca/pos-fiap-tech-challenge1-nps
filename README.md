# Tech Challenge · Fase 1 — NPS Preditivo

Análise da satisfação de clientes de um e-commerce a partir do **NPS** (Net Promoter Score) e construção de um **modelo preditivo de risco de detrator**, para que a empresa consiga agir **antes** de a pesquisa chegar ao cliente.

O projeto segue o ciclo **CRISP-DM**: entendimento do negócio, entendimento e preparação dos dados, modelagem, avaliação e proposta de implantação.

---

## 🎯 Objetivo

| | |
|---|---|
| **Problema de negócio** | O NPS da empresa é de **−80**: 84% dos clientes são detratores. A empresa só descobre a insatisfação depois que ela aconteceu. |
| **Pergunta de negócio** | Quais pontos da jornada de compra transformam clientes em detratores, e como antecipar esse risco? |
| **Objetivo analítico** | 1) Identificar, com análise exploratória e testes estatísticos, os fatores associados às notas baixas. 2) Construir um modelo que estime, para cada pedido, a **probabilidade de o cliente se tornar detrator** (nota de 0 a 6). |
| **Uso esperado** | Uma lista diária de pedidos priorizados por risco para o SAC e o CRM agirem de forma proativa (aviso de atraso, contato, compensação). |

---

## 🗃️ Descrição da base

Arquivo: `data/desafio_nps_fase_1.csv` — **2.500 pedidos** (1 linha por pedido), **19 colunas**, sem valores nulos.

| Grupo | Colunas |
|---|---|
| Identificação | `customer_id`, `order_id` |
| Perfil do cliente | `customer_age`, `customer_region`, `customer_tenure_months` |
| Pedido | `order_value`, `items_quantity`, `discount_value`, `payment_installments`, `freight_value` |
| Entrega | `delivery_time_days`, `delivery_delay_days`, `delivery_attempts` |
| Atendimento | `customer_service_contacts`, `complaints_count`, `resolution_time_days` |
| Satisfação e resultado | `nps_score` (0 a 10), `csat_internal_score`, `repeat_purchase_30d` |

O dicionário completo está em [`data/dicionario_de_dados.md`](data/dicionario_de_dados.md).

> ⚠️ A base tem **sinais de ter sido simulada**: notas de NPS com casas decimais, distribuições regulares demais e a coluna `repeat_purchase_30d` calculada diretamente a partir da nota. A direção dos achados é confiável; a intensidade dos efeitos e o desempenho do modelo tendem a ser menores em dados reais.

---

## 🧭 Metodologia

### 1. Entendimento do negócio e definição da target
- Variável-alvo: **`nps_score`**, transformada pela metodologia oficial do NPS em **Detrator (0–6)**, **Neutro (7–8)** e **Promotor (9–10)**.
- Para o modelo: `detrator = 1` se a nota for de 0 a 6.

### 2. Análise exploratória — `notebooks/01_eda_nps.ipynb`
Qualidade dos dados (completude, consistência, validade), estatísticas descritivas, distribuições (normal, Poisson, uniforme, binomial), intervalos de confiança (Z, t, bootstrap, Wilson), testes de hipótese (t, Mann-Whitney, ANOVA, Kruskal-Wallis, Qui-quadrado, Spearman), probabilidade condicional, regressão linear múltipla (OLS) e desenho de um teste A/B.

### 3. Modelagem — `notebooks/02_modelo_preditivo_nps.ipynb`
- **Seleção de variáveis pelo momento em que são conhecidas.** Ficam de fora por **vazamento de dados**: `repeat_purchase_30d` (posterior à pesquisa e derivada da nota) e `csat_internal_score` (outra medida de satisfação).
- **Dois cenários:** **A** (só o que se sabe na entrega) e **B** (soma os dados do atendimento).
- **Separação:** 80% treino / 20% teste, estratificada, `random_state=42`; escolha do modelo por **validação cruzada estratificada de 5 partes** no treino.
- **Preparação em `Pipeline` + `ColumnTransformer`:** `SimpleImputer`, `StandardScaler` e `OneHotEncoder`, ajustados só no treino.
- **Modelos comparados:** modelo "bobo", regra de negócio (atraso ≥ 1 dia), Regressão Logística, Árvore de Decisão e Random Forest. Complemento: regressão da nota (Linear × Árvore).
- **Avaliação:** AUC-ROC (principal), precisão, recall, F1, matriz de confusão, varredura de ponto de corte, valor esperado e lift/curva de ganho. A acurácia **não** é usada como critério, porque 84% dos pedidos já são detratores.

### 4. Pipeline de uso — `src/pipeline.py`
Script que reproduz o treino, salva o modelo em `models/` e pontua novos pedidos, gerando a lista priorizada por faixa de risco.

---

## 📊 Principais resultados

**Análise exploratória**
- NPS de **−80** (IC 95%: −82 a −78): 84,4% detratores, 11,2% neutros, 4,4% promotores.
- **89% dos pedidos atrasam.** O atraso é o fator nº 1 da insatisfação, agravado por reclamações e pela demora na resolução.
- Perfil do cliente, região, preço, frete e desconto **não** mudam a nota de forma relevante.

**Modelo (500 pedidos de teste, nunca vistos no treino)**

| Modelo | AUC-ROC | Precisão | Recall |
|---|---|---|---|
| Modelo bobo (sempre detrator) | 0,500 | 0,844 | 1,000 |
| Regra: atraso ≥ 1 dia | 0,784 | 0,881 | 0,929 |
| Logística · cenário A (entrega) | 0,779 | 0,861 | 0,967 |
| **Logística · cenário B (entrega + atendimento)** | **0,868** | **0,886** | **0,955** |
| Random Forest · cenário B | 0,869 | 0,872 | 0,981 |

- **Na entrega, a regra simples "atrasou, é risco" já basta**: nenhum modelo do cenário A a supera.
- **Com os dados de atendimento, a Regressão Logística sobe para AUC de 0,868.** A Random Forest empata, então foi escolhido o modelo mais simples e explicável.
- Fatores que mais aumentam o risco (razão de chances por +1 desvio-padrão): **atraso ×4,7**, **reclamações ×3,3**, **tempo de resolução ×2,0**.
- No corte de 0,90, o modelo aciona 64% dos pedidos com **96,6% de precisão**. Num cenário de custos **ilustrativo**, gera cerca de **2×** o valor da regra de atraso.

| Faixa de risco | % dos pedidos | Detratores reais | Ação sugerida |
|---|---|---|---|
| Alto (≥ 0,90) | 64,2% | 96,6% | Contato ativo do SAC + compensação |
| Médio (0,70–0,90) | 20,6% | 72,8% | Aviso proativo com novo prazo |
| Baixo (< 0,70) | 15,2% | 48,7% | Fluxo padrão |

---

## 📁 Estrutura do repositório

```
pos-fiap-tech-challenge1-nps/
├── data/
│   ├── desafio_nps_fase_1.csv          # base original do desafio
│   └── dicionario_de_dados.md          # descrição das colunas
├── notebooks/
│   ├── 01_eda_nps.ipynb                # tratamento, qualidade e análise exploratória
│   └── 02_modelo_preditivo_nps.ipynb   # preparação, modelagem, avaliação e uso
├── models/
│   ├── modelo_detrator_logistica.joblib  # pipeline final (preparação + modelo)
│   └── metricas_teste.json               # métricas no conjunto de teste
├── reports/
│   ├── Desafio_NPS_Fase1_Partes_1_a_5.docx  # relatório completo
│   ├── Desafio_NPS_Fase1_Partes_1_a_5.pdf
│   └── figuras/                             # gráficos principais
├── src/
│   └── pipeline.py                     # treino e pontuação fora do notebook
├── requirements.txt
└── README.md
```

---

## ▶️ Como reproduzir

### Opção 1 — Google Colab
1. Abra o notebook desejado no Colab (*Arquivo → Abrir notebook → GitHub*, colando a URL deste repositório).
2. Execute *Ambiente de execução → Executar tudo*.
3. Quando a janela de upload abrir, envie o arquivo `data/desafio_nps_fase_1.csv`.

### Opção 2 — Ambiente local
```bash
git clone https://github.com/sbrunofranca/pos-fiap-tech-challenge1-nps.git
cd pos-fiap-tech-challenge1-nps
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Notebooks (execute a partir da pasta notebooks/)
jupyter notebook notebooks/

# Pipeline: treina, avalia e salva o modelo em models/
python src/pipeline.py treinar

# Pontua pedidos e gera a lista priorizada por risco
python src/pipeline.py pontuar --entrada data/desafio_nps_fase_1.csv --saida reports/pedidos_pontuados.csv
```

Todos os sorteios usam `random_state=42`, então os resultados são reproduzíveis.

---

## ⚠️ Limitações

- **Dados com sinais de simulação**: o desempenho real tende a ser menor.
- **Momento das variáveis de atendimento não confirmado**: se reclamações e contatos forem registrados depois da pesquisa, o cenário B tem vazamento e vale apenas a regra de atraso.
- **Base sem datas**: não foi possível fazer validação temporal nem avaliar sazonalidade.
- **Valores financeiros hipotéticos** na análise de ponto de corte.
- **Associação não é causa**: o modelo indica quem está em risco; o efeito da ação proativa deve ser comprovado com **teste A/B** (≈ 750 pedidos atrasados por grupo, meta de 88% → 83% de detratores).
- **Uso indevido a evitar**: o score nunca deve ser usado para escolher quem recebe a pesquisa de NPS.

## 🔜 Próximos passos
1. Validar com o SAC o momento de registro das reclamações.
2. Obter datas dos pedidos para validação temporal.
3. Definir custos reais e capacidade do SAC para fixar o ponto de corte.
4. Calibrar as probabilidades antes do deploy.
5. Rodar o teste A/B do aviso proativo usando o score.
6. Monitorar AUC, taxa de detratores por faixa e *data drift*, com retreino periódico.

---

## 👥 Integrantes

| Nome | RM |
|---|---|
| Bruno Silva França | rm378898|

Projeto desenvolvido para o Tech Challenge da Fase 1 da pós-graduação.
