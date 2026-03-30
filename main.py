import logging
from datetime import datetime, timedelta
from collections import defaultdict

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================================================
# CONFIGURAÇÕES
# =========================================================

TOKEN_TELEGRAM = "8620256908:AAEhFfUsjQYlLFOziUc6FmwnNxKz8JbR5Uw"
CHAT_ID_ENVIO_AUTOMATICO = 5073956680  # seu chat_id

LINK_PLANILHA = "https://docs.google.com/spreadsheets/d/1Kp0qogeExlL3POt8zb9x2O2yTzRuYlg9hCa8eW_tbMk/edit?hl=pt-br&gid=0#gid=0"
CAMINHO_CRED = r"C:\Users\allan\OneDrive\Documentos\CredenciaisSeguras\monte-sinai-estoque-435d287fd76c.json"

NOME_ABA_ESTOQUE = "Estoque"
NOME_ABA_ENTRADAS = "Entradas"

COL_PRODUTO = "Produto"
COL_CODIGO = "Codigo"
COL_UNIDADE = "Peso Unidade"
COL_ESTOQUE = "Estoque Atual (g)"
COL_VALIDADE = "Validade"

# Na aba Entradas, ajuste se estiver diferente
COL_CODIGO_ENTRADA = "Código do Produto"      # se sua aba estiver sem acento, troque para "Codigo"
COL_QUANTIDADE_ENTRADA = "Quantidade"

LIMITE_GRAMAS = 5000
LIMITE_UNIDADE = 10
DIAS_ALERTA_VALIDADE = 10
LIMITE_MSG = 3800

# automático a cada 3 dias
INTERVALO_ENVIO_DIAS = 3

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def categoria_por_codigo(codigo: str) -> str:
    if not codigo:
        return "Outros"

    prefixo = str(codigo).split("-")[0].strip().upper()
    mapa = {
        "SAB": "Sabonetes",
        "GEL": "Géis",
        "OLE": "Óleos",
        "PO": "Pós",
        "ERV": "Ervas",
        "GRA": "Grãos e sementes",
        "TEM": "Temperos",
        "CAS": "Cascas",
        "LEI": "Leites",
        "MIX": "Mix",
        "SAL": "Sais",
        "FAR": "Farinhas",
        "CHA": "Chás",
        "EXT": "Extratos",
        "XAR": "Xaropes",
        "UNI": "Diversos",
    }
    return mapa.get(prefixo, "Outros")


def emoji_categoria(categoria: str) -> str:
    mapa = {
        "Sabonetes": "🧼",
        "Géis": "🧴",
        "Óleos": "🛢️",
        "Pós": "🌾",
        "Ervas": "🍃",
        "Grãos e sementes": "🌰",
        "Temperos": "🧂",
        "Cascas": "🌿",
        "Leites": "🥥",
        "Mix": "🥣",
        "Sais": "🧂",
        "Farinhas": "🌽",
        "Chás": "🍵",
        "Extratos": "💧",
        "Xaropes": "🍯",
        "Diversos": "📦",
        "Outros": "📌",
    }
    return mapa.get(categoria, "📌")


def formatar_numero(valor) -> str:
    try:
        valor = float(valor)
        if valor.is_integer():
            return str(int(valor))
        return f"{valor:.2f}".rstrip("0").rstrip(".")
    except Exception:
        return "0"


def normalizar_unidade(valor: str) -> str:
    texto = str(valor).strip().lower()
    if texto in ["g", "gr", "grama", "gramas"]:
        return "g"
    if texto in ["un", "und", "unid", "unidade", "unidades"]:
        return "un"
    return texto


def parse_estoque(valor) -> float:
    try:
        texto = str(valor).strip().replace(",", ".")
        if not texto:
            return 0.0
        return float(texto)
    except Exception:
        return 0.0


def parse_quantidade(valor) -> float:
    try:
        texto = str(valor).strip().replace(",", ".")
        if not texto:
            return 0.0
        return float(texto)
    except Exception:
        return 0.0


def parse_validade(valor):
    if valor is None or str(valor).strip() == "":
        return None

    texto = str(valor).strip()
    formatos = ["%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]

    for formato in formatos:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue

    return None


def ordenar_grupos(grupos_dict):
    return dict(sorted(grupos_dict.items(), key=lambda x: x[0]))


def montar_linha_item(produto: str, codigo: str, estoque: float, unidade: str) -> str:
    return f"• {produto} ({codigo}) — {formatar_numero(estoque)} {unidade}"


def quebrar_mensagem(texto: str, limite: int = LIMITE_MSG) -> list[str]:
    partes = []
    atual = ""

    for linha in texto.split("\n"):
        candidata = atual + linha + "\n"
        if len(candidata) > limite:
            if atual.strip():
                partes.append(atual.strip())
            atual = linha + "\n"
        else:
            atual = candidata

    if atual.strip():
        partes.append(atual.strip())

    return partes


async def responder_texto_grande(update: Update, texto: str):
    partes = quebrar_mensagem(texto)
    total = len(partes)

    for i, parte in enumerate(partes, start=1):
        cabecalho = f"📨 Parte {i}/{total}\n\n" if total > 1 else ""
        await update.message.reply_text(cabecalho + parte)


async def enviar_texto_grande_para_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int, texto: str):
    partes = quebrar_mensagem(texto)
    total = len(partes)

    for i, parte in enumerate(partes, start=1):
        cabecalho = f"📨 Parte {i}/{total}\n\n" if total > 1 else ""
        await context.bot.send_message(chat_id=chat_id, text=cabecalho + parte)

# =========================================================
# LEITURA E PROCESSAMENTO
# =========================================================

def conectar_planilha():
    credenciais = ServiceAccountCredentials.from_json_keyfile_name(CAMINHO_CRED, scope)
    cliente = gspread.authorize(credenciais)
    return cliente.open_by_url(LINK_PLANILHA)


def carregar_dados_estoque() -> pd.DataFrame:
    sheet = conectar_planilha()
    aba_estoque = sheet.worksheet(NOME_ABA_ESTOQUE)
    dados = aba_estoque.get_all_records()
    return pd.DataFrame(dados)


def carregar_codigos_com_entrada() -> set:
    sheet = conectar_planilha()
    aba_entradas = sheet.worksheet(NOME_ABA_ENTRADAS)
    dados_entradas = aba_entradas.get_all_records()
    df_entradas = pd.DataFrame(dados_entradas)

    if df_entradas.empty:
        return set()

    codigos = set()

    for _, row in df_entradas.iterrows():
        codigo = str(row.get(COL_CODIGO_ENTRADA, "")).strip()
        quantidade = parse_quantidade(row.get(COL_QUANTIDADE_ENTRADA, 0))

        if codigo and quantidade > 0:
            codigos.add(codigo)

    return codigos


def processar_alertas(df: pd.DataFrame, codigos_com_entrada: set) -> dict:
    grupos_un = defaultdict(list)
    grupos_g = defaultdict(list)
    criticos = []
    validades = []

    total_baixo = 0
    total_criticos = 0
    total_validade = 0
    contagem_categorias = defaultdict(int)

    hoje = datetime.now().date()
    data_limite_validade = hoje + timedelta(days=DIAS_ALERTA_VALIDADE)

    for _, row in df.iterrows():
        produto = str(row.get(COL_PRODUTO, "")).strip()
        codigo = str(row.get(COL_CODIGO, "")).strip()
        unidade = normalizar_unidade(row.get(COL_UNIDADE, ""))
        estoque = parse_estoque(row.get(COL_ESTOQUE, 0))
        categoria = categoria_por_codigo(codigo)

        if not produto or not codigo:
            continue

        # FILTRO: só alerta produto que já teve entrada
        if codigo not in codigos_com_entrada:
            continue

        item_em_alerta_estoque = False

        if unidade == "g" and estoque < LIMITE_GRAMAS:
            grupos_g[categoria].append(montar_linha_item(produto, codigo, estoque, "g"))
            total_baixo += 1
            contagem_categorias[categoria] += 1
            item_em_alerta_estoque = True

        elif unidade == "un" and estoque < LIMITE_UNIDADE:
            grupos_un[categoria].append(montar_linha_item(produto, codigo, estoque, "un"))
            total_baixo += 1
            contagem_categorias[categoria] += 1
            item_em_alerta_estoque = True

        if item_em_alerta_estoque and estoque <= 0:
            criticos.append(montar_linha_item(produto, codigo, estoque, unidade))
            total_criticos += 1

        validade_bruta = row.get(COL_VALIDADE, "")
        validade = parse_validade(validade_bruta)

        if validade and validade.date() <= data_limite_validade:
            dias_para_vencer = (validade.date() - hoje).days

            if dias_para_vencer < 0:
                status = f"vencido há {abs(dias_para_vencer)} dia(s)"
            elif dias_para_vencer == 0:
                status = "vence hoje"
            else:
                status = f"vence em {dias_para_vencer} dia(s)"

            validades.append(
                f"• {produto} ({codigo}) — {str(validade_bruta).strip()} ({status})"
            )
            total_validade += 1

    return {
        "grupos_un": grupos_un,
        "grupos_g": grupos_g,
        "criticos": criticos,
        "validades": validades,
        "total_baixo": total_baixo,
        "total_criticos": total_criticos,
        "total_validade": total_validade,
        "contagem_categorias": contagem_categorias,
    }


def obter_resultado() -> dict:
    df = carregar_dados_estoque()

    if df.empty:
        return {"vazio": True}

    codigos_com_entrada = carregar_codigos_com_entrada()
    resultado = processar_alertas(df, codigos_com_entrada)
    resultado["vazio"] = False
    return resultado

# =========================================================
# MONTAGEM DAS MENSAGENS
# =========================================================

def montar_resumo_executivo(resultado: dict) -> str:
    partes = [
        "🚨 ALERTA CORPORATIVO DE ESTOQUE",
        "MONTE SINAI ERVAS",
        f"🕒 Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        "📊 RESUMO EXECUTIVO",
        f"• Itens com estoque abaixo do limite: {resultado['total_baixo']}",
        f"• Itens críticos/zerados: {resultado['total_criticos']}",
        f"• Itens com validade próxima: {resultado['total_validade']}",
    ]

    if resultado["contagem_categorias"]:
        top = sorted(
            resultado["contagem_categorias"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        partes.append("")
        partes.append("🏷️ TOP CATEGORIAS COM ALERTA")
        for categoria, quantidade in top:
            partes.append(f"• {categoria}: {quantidade}")

    return "\n".join(partes)


def montar_bloco_categorias(titulo: str, grupos: dict) -> list[str]:
    partes = [titulo]
    for categoria, itens in ordenar_grupos(grupos).items():
        partes.append(f"\n{emoji_categoria(categoria)} {categoria}")
        partes.extend(itens)
    return partes


def montar_detalhamento_operacional(resultado: dict) -> str:
    partes = [
        "📦 DETALHAMENTO OPERACIONAL",
        "MONTE SINAI ERVAS"
    ]

    if resultado["grupos_un"]:
        partes.append("")
        partes.extend(montar_bloco_categorias("🔹 ESTOQUE BAIXO — ITENS POR UNIDADE", resultado["grupos_un"]))

    if resultado["grupos_g"]:
        partes.append("")
        partes.extend(montar_bloco_categorias("🔹 ESTOQUE BAIXO — ITENS POR PESO", resultado["grupos_g"]))

    if resultado["criticos"]:
        partes.append("")
        partes.append("❗ ITENS CRÍTICOS / ZERADOS")
        partes.extend(resultado["criticos"])

    if resultado["validades"]:
        partes.append("")
        partes.append(f"📅 VALIDADE PRÓXIMA — ATÉ {DIAS_ALERTA_VALIDADE} DIAS")
        partes.extend(resultado["validades"])

    if not any([resultado["grupos_un"], resultado["grupos_g"], resultado["criticos"], resultado["validades"]]):
        partes.append("")
        partes.append("Sem alertas no momento.")

    return "\n".join(partes)


def montar_criticos(resultado: dict) -> str:
    partes = ["❗ ITENS CRÍTICOS / ZERADOS", ""]
    if resultado["criticos"]:
        partes.extend(resultado["criticos"])
    else:
        partes.append("Sem itens críticos no momento.")
    return "\n".join(partes)


def montar_validades(resultado: dict) -> str:
    partes = [f"📅 VALIDADE PRÓXIMA — ATÉ {DIAS_ALERTA_VALIDADE} DIAS", ""]
    if resultado["validades"]:
        partes.extend(resultado["validades"])
    else:
        partes.append("Sem itens com validade próxima.")
    return "\n".join(partes)


def montar_categorias(resultado: dict) -> str:
    partes = ["🏷️ CATEGORIAS COM ALERTA", ""]
    if resultado["contagem_categorias"]:
        ranking = sorted(
            resultado["contagem_categorias"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for categoria, quantidade in ranking:
            partes.append(f"• {categoria}: {quantidade}")
    else:
        partes.append("Sem categorias em alerta.")
    return "\n".join(partes)

# =========================================================
# COMANDOS DO BOT
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "🤖 Bot de Estoque Monte Sinai\n\n"
        "Comandos disponíveis:\n"
        "/resumo - resumo executivo\n"
        "/detalhamento - relatório completo\n"
        "/criticos - só itens zerados/críticos\n"
        "/validade - itens com validade próxima\n"
        "/categorias - ranking por categoria\n"
        "/estoque - resumo + detalhamento\n"
        "/ajuda - mostrar comandos"
    )
    await update.message.reply_text(texto)


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = obter_resultado()
    if resultado["vazio"]:
        await update.message.reply_text("A aba de estoque está vazia.")
        return
    await update.message.reply_text(montar_resumo_executivo(resultado))


async def detalhamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = obter_resultado()
    if resultado["vazio"]:
        await update.message.reply_text("A aba de estoque está vazia.")
        return
    await responder_texto_grande(update, montar_detalhamento_operacional(resultado))


async def criticos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = obter_resultado()
    if resultado["vazio"]:
        await update.message.reply_text("A aba de estoque está vazia.")
        return
    await responder_texto_grande(update, montar_criticos(resultado))


async def validade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = obter_resultado()
    if resultado["vazio"]:
        await update.message.reply_text("A aba de estoque está vazia.")
        return
    await responder_texto_grande(update, montar_validades(resultado))


async def categorias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = obter_resultado()
    if resultado["vazio"]:
        await update.message.reply_text("A aba de estoque está vazia.")
        return
    await update.message.reply_text(montar_categorias(resultado))


async def estoque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = obter_resultado()
    if resultado["vazio"]:
        await update.message.reply_text("A aba de estoque está vazia.")
        return
    await update.message.reply_text(montar_resumo_executivo(resultado))
    await responder_texto_grande(update, montar_detalhamento_operacional(resultado))

# =========================================================
# ENVIO AUTOMÁTICO
# =========================================================

async def envio_automatico(context: ContextTypes.DEFAULT_TYPE):
    try:
        resultado = obter_resultado()

        if resultado["vazio"]:
            return

        tem_alerta = any([
            resultado["grupos_un"],
            resultado["grupos_g"],
            resultado["criticos"],
            resultado["validades"]
        ])

        if not tem_alerta:
            return

        resumo_texto = montar_resumo_executivo(resultado)
        detalhamento_texto = montar_detalhamento_operacional(resultado)

        await context.bot.send_message(
            chat_id=CHAT_ID_ENVIO_AUTOMATICO,
            text=resumo_texto
        )

        await enviar_texto_grande_para_chat(
            context=context,
            chat_id=CHAT_ID_ENVIO_AUTOMATICO,
            texto=detalhamento_texto
        )

    except Exception as e:
        print(f"Erro no envio automático: {e}")

# =========================================================
# MAIN
# =========================================================

def main():
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("resumo", resumo))
    app.add_handler(CommandHandler("detalhamento", detalhamento))
    app.add_handler(CommandHandler("criticos", criticos))
    app.add_handler(CommandHandler("validade", validade))
    app.add_handler(CommandHandler("categorias", categorias))
    app.add_handler(CommandHandler("estoque", estoque))

    # envio automático a cada 3 dias
    job_queue = app.job_queue
    job_queue.run_repeating(
        envio_automatico,
        interval=INTERVALO_ENVIO_DIAS * 24 * 60 * 60,
        first=10
    )

    print("Bot rodando...")
    app.run_polling()


if __name__ == "__main__":
    main()