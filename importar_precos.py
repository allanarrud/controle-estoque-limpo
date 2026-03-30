import pandas as pd
import mysql.connector

conexao = mysql.connector.connect(
    host="localhost",
    user="root",
    password="senhafacil",
    database="monte_sinai"
)

cursor = conexao.cursor()

df = pd.read_csv("obs_preco.csv")

# limpa nomes das colunas
df.columns = df.columns.str.strip()

# remove coluna extra se existir
if "Unnamed: 0" in df.columns:
    df = df.drop(columns=["Unnamed: 0"])

print("Colunas:", df.columns.tolist())

# converte preço de '6,92' para 6.92
df["Preco"] = (
    df["Preco"]
    .astype(str)
    .str.replace(".", "", regex=False)   # remove separador de milhar, se houver
    .str.replace(",", ".", regex=False)  # troca vírgula por ponto
)

df["Preco"] = pd.to_numeric(df["Preco"], errors="coerce")

# remove linhas com preço inválido
df = df.dropna(subset=["Preco"])

# limpar tabela antes
cursor.execute("DELETE FROM precos_fornecedores")

for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO precos_fornecedores (codigo, produto, fornecedor, preco)
        VALUES (%s, %s, %s, %s)
    """, (
        row["Codigo"],
        row["Produto"],
        row["empresa"],
        float(row["Preco"])
    ))

conexao.commit()

print("Importação de preços concluída!")

cursor.close()
conexao.close()