import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="senhafacil",
    database="monte_sinai"
)

cursor = conn.cursor()

df = pd.read_csv("Entradas.csv", encoding="utf-8")

print("Colunas do CSV:", df.columns.tolist())

# converte data
df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
df = df.dropna(subset=["Data"])
df["Data"] = df["Data"].dt.strftime("%Y-%m-%d")

# debug
print("\nValores nulos por coluna:")
print(df.isna().sum())

cursor.execute("DELETE FROM entradas")

for _, row in df.iterrows():
    data = row["Data"]
    codigo = None if pd.isna(row["Código do Produto"]) else str(row["Código do Produto"]).strip()
    produto = None if pd.isna(row["Produto"]) else str(row["Produto"]).strip()
    unidade = None if pd.isna(row["Unidade"]) else str(row["Unidade"]).strip().lower()
    quantidade = None if pd.isna(row["Quantidade"]) else float(row["Quantidade"])
    observacao = None if pd.isna(row["Observação"]) else str(row["Observação"]).strip()

    cursor.execute("""
        INSERT INTO entradas (
            data_entrada,
            codigo_produto,
            produto,
            unidade_medida,
            quantidade,
            observacao
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data,
        codigo,
        produto,
        unidade,
        quantidade,
        observacao
    ))

conn.commit()
cursor.close()
conn.close()

print("Entradas importadas com sucesso 🚀")