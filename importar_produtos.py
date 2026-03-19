import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="senha",
    database="monte_sinai"
)

cursor = conn.cursor()

# ajuste o nome do arquivo se necessário
df = pd.read_csv("MONTE SINAI ERVAS - Produtos_mysql.csv", encoding="utf-8")

# opcional: ver nomes das colunas
print("Colunas do CSV:", df.columns.tolist())

# limpar tabela antes
cursor.execute("DELETE FROM produtos")

for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO produtos (codigo, produto, unidade_medida, estoque_minimo, validade_dias)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        row["codigo"],
        row["produto"],
        row["unidade_medida"],
        row["estoque_minimo"],
        None if pd.isna(row["validade_dias"]) else row["validade_dias"]
    ))

conn.commit()
cursor.close()
conn.close()

print("Produtos importados com sucesso 🚀")