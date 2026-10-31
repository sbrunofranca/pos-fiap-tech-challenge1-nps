"""
Pipeline do modelo de risco de detrator (Desafio NPS - Fase 1).

Reproduz, fora do notebook, as etapas de preparação, treino, avaliação e uso
definidas em notebooks/02_modelo_preditivo_nps.ipynb.

Uso (a partir da raiz do repositório):
    python src/pipeline.py treinar
    python src/pipeline.py pontuar --entrada data/desafio_nps_fase_1.csv --saida reports/pedidos_pontuados.csv
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_DADOS = RAIZ / "data" / "desafio_nps_fase_1.csv"
ARQUIVO_MODELO = RAIZ / "models" / "modelo_detrator_logistica.joblib"
ARQUIVO_METRICAS = RAIZ / "models" / "metricas_teste.json"

# Variáveis de entrada (cenário B: entrega + atendimento).
# Ficam de fora: IDs, csat_internal_score e repeat_purchase_30d (vazamento de dados).
VARIAVEIS_NUMERICAS = [
    "customer_age", "customer_tenure_months", "order_value", "items_quantity",
    "discount_value", "payment_installments", "freight_value",
    "delivery_time_days", "delivery_delay_days", "delivery_attempts",
    "customer_service_contacts", "complaints_count", "resolution_time_days",
]
VARIAVEIS_CATEGORICAS = ["customer_region"]
COLUNAS_ENTRADA = VARIAVEIS_NUMERICAS + VARIAVEIS_CATEGORICAS

# Faixas de risco (parâmetros de negócio; ajustar à capacidade do SAC e aos custos reais)
LIMITE_RISCO_MEDIO = 0.70
LIMITE_RISCO_ALTO = 0.90
ACOES = {
    "Alto": "Contato ativo do SAC + compensação",
    "Médio": "Aviso proativo por mensagem",
    "Baixo": "Fluxo padrão",
}


def carregar_dados(caminho=ARQUIVO_DADOS):
    """Lê a base de pedidos."""
    return pd.read_csv(caminho)


def criar_alvo(df):
    """Target binária: 1 = detrator (nota de 0 a 6), 0 = neutro ou promotor."""
    return (df["nps_score"] < 7).astype(int)


def criar_pipeline():
    """Preparação (imputação, padronização, dummies) + Regressão Logística."""
    numerico = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorico = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocessamento = ColumnTransformer([
        ("num", numerico, VARIAVEIS_NUMERICAS),
        ("cat", categorico, VARIAVEIS_CATEGORICAS),
    ])
    return Pipeline([
        ("preprocessamento", preprocessamento),
        ("modelo", LogisticRegression(max_iter=1000, random_state=SEED)),
    ])


def treinar():
    """Avalia no teste (80/20 estratificado) e depois retreina com a base inteira."""
    df = carregar_dados()
    X, y = df[COLUNAS_ENTRADA], criar_alvo(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y)

    # 1) Avaliação honesta: treina só com o treino e mede no teste
    pipeline = criar_pipeline().fit(X_train, y_train)
    score = pipeline.predict_proba(X_test)[:, 1]
    previsto = (score >= 0.5).astype(int)
    regra_atraso = (X_test["delivery_delay_days"] >= 1).astype(int)
    metricas = {
        "modelo_logistica": {
            "auc_roc": roc_auc_score(y_test, score),
            "acuracia": accuracy_score(y_test, previsto),
            "precision": precision_score(y_test, previsto),
            "recall": recall_score(y_test, previsto),
            "f1": f1_score(y_test, previsto),
        },
        "regra_atraso_1_dia": {
            "auc_roc": roc_auc_score(y_test, X_test["delivery_delay_days"]),
            "precision": precision_score(y_test, regra_atraso),
            "recall": recall_score(y_test, regra_atraso),
        },
        "taxa_detratores_teste": float(y_test.mean()),
    }

    # 2) Modelo final: retreina com todos os dados e salva o pipeline completo
    modelo_final = criar_pipeline().fit(X, y)
    ARQUIVO_MODELO.parent.mkdir(exist_ok=True)
    joblib.dump(modelo_final, ARQUIVO_MODELO)
    ARQUIVO_METRICAS.write_text(json.dumps(metricas, indent=2, ensure_ascii=False))

    print(json.dumps(metricas, indent=2, ensure_ascii=False))
    print(f"\nModelo salvo em {ARQUIVO_MODELO.relative_to(RAIZ)}")


def pontuar(novos_pedidos, caminho_modelo=ARQUIVO_MODELO):
    """Calcula o risco de detração, a faixa de risco e a ação sugerida por pedido."""
    modelo = joblib.load(caminho_modelo)
    resultado = novos_pedidos[["order_id"]].copy()
    resultado["risco_detrator"] = modelo.predict_proba(novos_pedidos[COLUNAS_ENTRADA])[:, 1]
    resultado["faixa_risco"] = pd.cut(
        resultado["risco_detrator"],
        bins=[0, LIMITE_RISCO_MEDIO, LIMITE_RISCO_ALTO, 1.0001],
        right=False, labels=["Baixo", "Médio", "Alto"])
    resultado["acao_sugerida"] = resultado["faixa_risco"].map(ACOES)
    return resultado.sort_values("risco_detrator", ascending=False)


def main():
    parser = argparse.ArgumentParser(description="Modelo de risco de detrator (NPS)")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("treinar", help="avalia, retreina e salva o modelo em models/")
    p = sub.add_parser("pontuar", help="pontua pedidos de um CSV")
    p.add_argument("--entrada", required=True, help="CSV com os pedidos a pontuar")
    p.add_argument("--saida", required=True, help="CSV de saída com risco e ação")
    args = parser.parse_args()

    if args.comando == "treinar":
        treinar()
    else:
        lista = pontuar(pd.read_csv(args.entrada))
        lista.to_csv(args.saida, index=False)
        print(lista["faixa_risco"].value_counts().sort_index())
        print(f"\nLista priorizada salva em {args.saida}")


if __name__ == "__main__":
    np.random.seed(SEED)
    main()
