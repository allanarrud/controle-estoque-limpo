import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="senha",
    database="monte_sinai"
)

cursor = conn.cursor()

# lê o CSV
df = pd.read_csv("Saidas.csv", encoding="utf-8")

print("Colunas do CSV:", df.columns.tolist())

# tratar data
df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
df = df.dropna(subset=["Data"])
df["Data"] = df["Data"].dt.strftime("%Y-%m-%d")

# tratar quantidade
df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce")

# manter só saídas reais
df = df[df["Quantidade"].notna()]
df = df[df["Quantidade"] > 0]

# trocar NaN por None
df = df.where(pd.notna(df), None)

# buscar unidade direto do banco
cursor.execute("SELECT codigo, unidade_medida FROM produtos")
unidades = dict(cursor.fetchall())

# limpar tabela antes
cursor.execute("DELETE FROM saidas")

for _, row in df.iterrows():
    codigo = str(row["Código"]).strip()
    produto = str(row["Produto"]).strip()
    funcionario = None if row["Funcionario"] is None else str(row["Funcionario"]).strip()

    unidade = unidades.get(codigo)

    # se o código não existir em produtos, ignora e avisa
    if unidade is None:
        print(f"⚠ Código não encontrado em produtos: {codigo} - {produto}")
        continue

    cursor.execute("""
        INSERT INTO saidas (
            data_saida,
            codigo_produto,
            produto,
            unidade_medida,
            quantidade,
            funcionario,
            validade
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        row["Data"],
        codigo,
        produto,
        unidade,
        float(row["Quantidade"]),
        funcionario,
        None
    ))

conn.commit()
cursor.close()
conn.close()

print("Saídas importadas com sucesso 🚀")