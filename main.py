import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import pywhatkit
from datetime import datetime, timedelta

# CONFIGURAÇÕES

LINK_PLANILHA = "https://docs.google.com/spreadsheets/d/1Kp0qogeExlL3POt8zb9x2O2yTzRuYlg9hCa8eW_tbMk/edit?hl=pt-br&gid=0#gid=0"
NUMERO_WPP = "+5591992945159"
LIMITE_GRAMAS = 5000
LIMITE_UNIDADE = 10

# AUTENTICAÇÃO GOOGLE SHEETS

CAMINHO_CRED = r"C:\Users\allan\OneDrive\Documentos\CredenciaisSeguras\monte-sinai-estoque-435d287fd76c.json"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credenciais = ServiceAccountCredentials.from_json_keyfile_name(
    CAMINHO_CRED, scope
    
)

cliente = gspread.authorize(credenciais)
sheet = cliente.open_by_url(LINK_PLANILHA)
aba_estoque = sheet.worksheet("Estoque")

# LEITURA DO ESTOQUE

dados = aba_estoque.get_all_records()
df = pd.DataFrame(dados)

# FILTRO DE ALERTA

alertas = []

for _, row in df.iterrows():
    produto = row["Produto"]
    codigo = row["Codigo"]
    peso_unid = str(row["Peso Unidade"]).strip().lower()

    try:
        estoque = float(row["Estoque Atual (g)"])
    except:
        estoque = 0

    if peso_unid == "g":
        if estoque < LIMITE_GRAMAS:
            alertas.append(
                f"{produto} ({codigo}) abaixo de {LIMITE_GRAMAS}g. Atual: {int(estoque)}g."
            )
    elif peso_unid == "un":
        if estoque < LIMITE_UNIDADE:
            alertas.append(
                f"{produto} ({codigo}) abaixo de {LIMITE_UNIDADE} un. Atual: {int(estoque)} un."
            )

    # VALIDADE PRÓXIMA

    if "Validade" in row and row["Validade"]:
        try:
            validade = datetime.strptime(row["Validade"], "%d/%m/%y")
            if validade.date() <= (datetime.now().date() + timedelta(days=10)):
                alertas.append(f"{produto} ({codigo}) com validade próxima: {row['Validade']}")
        except:
            pass

# ENVIO NO WHATSAPP

if alertas:
    mensagem = "*ALERTA DE ESTOQUE - MONTE SINAI ERVAS*\n\n" + "\n".join(alertas)

    # ENVIO IMEDIATO
    pywhatkit.sendwhatmsg_instantly(NUMERO_WPP, mensagem, wait_time=15)
    print("Mensagem enviada!")
else:
    print("Sem alertas no momento.")