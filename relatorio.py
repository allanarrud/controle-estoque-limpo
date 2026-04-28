import os
import pandas as pd
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# =========================================================
# CONFIGURAÇÕES
# =========================================================

LINK_PLANILHA = "https://docs.google.com/spreadsheets/d/1Kp0qogeExlL3POt8zb9x2O2yTzRuYlg9hCa8eW_tbMk/edit?hl=pt-br&gid=0#gid=0"
CAMINHO_CRED = r"C:\Users\allan\OneDrive\Documentos\CredenciaisSeguras\monte-sinai-estoque-435d287fd76c.json"
NOME_ABA_RELATORIOS = "Relatórios"

NOME_EMPRESA = "GM DataCore"
NOME_CLIENTE = "Monte Sinai Ervas"
NOME_ARQUIVO_LOGO = os.path.join("assets", "logo_montesinai.png")

COL_PRODUTO = "Produto"
COL_MEDIA_SAIDA = "Média saída diária"
COL_DATA_RUPTURA = "Data ruptura"
COL_STATUS_RUPTURA = "Status Ruptura"
COL_ESTOQUE_ATUAL = "Estoque Atual"
COL_PRIORIDADE_COMPRA = "Prioridade de compra"
COL_CODIGO = "Codigo"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def formatar_numero(valor) -> str:
    try:
        valor = float(valor)
        if valor.is_integer():
            return str(int(valor))
        return f"{valor:.2f}".rstrip("0").rstrip(".")
    except Exception:
        return "0"


def parse_numero_planilha(valor):
    try:
        if valor is None:
            return None

        texto = str(valor).strip()
        if not texto:
            return None

        texto = texto.replace(".", "").replace(",", ".")
        return float(texto)
    except Exception:
        return None


def parse_data_planilha(valor):
    if valor is None:
        return None

    texto = str(valor).strip()
    if not texto:
        return None

    formatos = ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y"]

    for formato in formatos:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue

    try:
        data = pd.to_datetime(texto, dayfirst=True, errors="coerce")
        if pd.isna(data):
            return None
        return data
    except Exception:
        return None


def prioridade_ordem(valor: str) -> int:
    prioridade = str(valor).strip().upper()

    if "URGENTE" in prioridade:
        return 1
    if "AGORA" in prioridade:
        return 2
    if "SEMANA" in prioridade:
        return 3
    if "PROGRAMAR" in prioridade:
        return 4
    return 99


def cor_prioridade(valor: str):
    prioridade = str(valor).strip().upper()

    if "URGENTE" in prioridade:
        return colors.HexColor("#FDECEC")
    if "AGORA" in prioridade:
        return colors.HexColor("#FEE2E2")
    if "SEMANA" in prioridade:
        return colors.HexColor("#FEF3C7")
    if "PROGRAMAR" in prioridade:
        return colors.HexColor("#ECFCCB")
    return colors.whitesmoke


# =========================================================
# CONEXÃO / LEITURA
# =========================================================

def conectar_planilha():
    credenciais = ServiceAccountCredentials.from_json_keyfile_name(CAMINHO_CRED, scope)
    cliente = gspread.authorize(credenciais)
    return cliente.open_by_url(LINK_PLANILHA)


def carregar_dados_relatorios() -> pd.DataFrame:
    sheet = conectar_planilha()
    aba_relatorios = sheet.worksheet(NOME_ABA_RELATORIOS)
    dados = aba_relatorios.get_all_records()
    return pd.DataFrame(dados)


# =========================================================
# PROCESSAMENTO
# =========================================================
def carregar_codigos_com_entrada() -> set:
    sheet = conectar_planilha()
    aba_entradas = sheet.worksheet("Entradas")

    dados = aba_entradas.get_all_records()
    df_entradas = pd.DataFrame(dados)

    if df_entradas.empty:
        return set()

    codigos = set()

    for _, row in df_entradas.iterrows():
        codigo = str(row.get("Código do Produto", "")).strip()
        quantidade = parse_numero_planilha(row.get("Quantidade"))

        if codigo and quantidade and quantidade > 0:
            codigos.add(codigo)

    return codigos

def preparar_relatorio(df: pd.DataFrame) -> pd.DataFrame:
    colunas_necessarias = [
        COL_PRODUTO,
        COL_CODIGO,
        COL_MEDIA_SAIDA,
        COL_DATA_RUPTURA,
        COL_STATUS_RUPTURA,
        COL_ESTOQUE_ATUAL,
        COL_PRIORIDADE_COMPRA,
    ]

    for col in colunas_necessarias:
        if col not in df.columns:
            raise ValueError(f"Coluna ausente na aba Relatórios: {col}")

    df = df.copy()

    codigos_com_entrada = carregar_codigos_com_entrada()

    # filtra só produtos que já tiveram entrada
    df = df[df[COL_CODIGO].astype(str).str.strip().isin(codigos_com_entrada)]

    # limpa linhas vazias
    df = df[df[COL_PRODUTO].astype(str).str.strip() != ""]
    df = df[df[COL_PRIORIDADE_COMPRA].astype(str).str.strip() != ""]
    df = df[df[COL_STATUS_RUPTURA].astype(str).str.strip() != ""]

    # converte tipos
    df[COL_MEDIA_SAIDA] = df[COL_MEDIA_SAIDA].apply(parse_numero_planilha)
    df[COL_ESTOQUE_ATUAL] = df[COL_ESTOQUE_ATUAL].apply(parse_numero_planilha)
    df[COL_DATA_RUPTURA] = df[COL_DATA_RUPTURA].apply(parse_data_planilha)

    # ordena por prioridade e data
    df["ordem_prioridade"] = df[COL_PRIORIDADE_COMPRA].apply(prioridade_ordem)
    df = df.sort_values(
        by=["ordem_prioridade", COL_DATA_RUPTURA],
        ascending=[True, True]
    )

    return df


def gerar_resumo(df: pd.DataFrame) -> dict:
    prioridades = df[COL_PRIORIDADE_COMPRA].astype(str).str.upper()

    return {
        "total_itens": len(df),
        "urgentes": prioridades.str.contains("URGENTE", na=False).sum(),
        "agora": prioridades.str.contains("AGORA", na=False).sum(),
        "semana": prioridades.str.contains("SEMANA", na=False).sum(),
        "programar": prioridades.str.contains("PROGRAMAR", na=False).sum(),
    }


# =========================================================
# PDF
# =========================================================

def gerar_pdf_relatorio_ruptura(df: pd.DataFrame, caminho_arquivo: str):
    resumo = gerar_resumo(df)

    doc = SimpleDocTemplate(
        caminho_arquivo,
        pagesize=landscape(A4),
        rightMargin=22,
        leftMargin=22,
        topMargin=24,
        bottomMargin=24
    )

    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        name="TituloCustom",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#111827"),
        alignment=TA_LEFT,
        spaceAfter=6,
    )

    subtitulo_style = ParagraphStyle(
        name="SubtituloCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4B5563"),
        alignment=TA_LEFT,
    )

    secao_style = ParagraphStyle(
        name="SecaoCustom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#111827"),
        alignment=TA_LEFT,
        spaceAfter=8,
    )

    card_style = ParagraphStyle(
        name="CardStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#111827"),
        alignment=TA_LEFT,
    )

    rodape_style = ParagraphStyle(
        name="RodapeCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#6B7280"),
        alignment=TA_CENTER,
    )

    elementos = []



    # Logo — sys._MEIPASS é definido pelo PyInstaller no modo frozen
    import sys
    BASE_DIR = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    CAMINHO_LOGO = os.path.join(BASE_DIR, NOME_ARQUIVO_LOGO)

    print("Caminho da logo:", CAMINHO_LOGO)
    print("Logo existe?", os.path.exists(CAMINHO_LOGO))

    if os.path.exists(CAMINHO_LOGO):
        try:
            logo = Image(CAMINHO_LOGO)
            logo.drawWidth = 90
            logo.drawHeight = 90
            elementos.append(logo)
            elementos.append(Spacer(1, 10))
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
    else:
            print(f"Logo não encontrada em: {CAMINHO_LOGO}")

    # Cabeçalho
    elementos.append(Paragraph("Relatório Executivo de Ruptura de Estoque", titulo_style))
    elementos.append(Paragraph(f"Cliente: {NOME_CLIENTE}", subtitulo_style))
    elementos.append(Paragraph(f"Emitido por: {NOME_EMPRESA}", subtitulo_style))
    elementos.append(
        Paragraph(
            f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            subtitulo_style
        )
    )
    elementos.append(Spacer(1, 16))

    # Resumo
    elementos.append(Paragraph("Resumo Executivo", secao_style))

    cards = [[
        Paragraph(f"<b>Total monitorado</b><br/>{resumo['total_itens']}", card_style),
        Paragraph(f"<b>Urgente</b><br/>{resumo['urgentes']}", card_style),
        Paragraph(f"<b>Comprar agora</b><br/>{resumo['agora']}", card_style),
        Paragraph(f"<b>Esta semana</b><br/>{resumo['semana']}", card_style),
        Paragraph(f"<b>Programar</b><br/>{resumo['programar']}", card_style),
    ]]

    tabela_cards = Table(cards, colWidths=[145, 110, 120, 110, 110])
    tabela_cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#D1D5DB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elementos.append(tabela_cards)
    elementos.append(Spacer(1, 18))

    # Tabela principal
    elementos.append(Paragraph("Detalhamento dos Itens", secao_style))

    dados = [[
        "Produto",
        "Média de saída",
        "Estoque atual",
        "Data de ruptura",
        "Status da ruptura",
        "Prioridade de compra"
    ]]

    for _, row in df.iterrows():
        data_fmt = "-"
        if row.get(COL_DATA_RUPTURA) is not None and not pd.isna(row.get(COL_DATA_RUPTURA)):
            if hasattr(row[COL_DATA_RUPTURA], "strftime"):
                data_fmt = row[COL_DATA_RUPTURA].strftime("%d/%m/%Y")

        media_diaria = row.get(COL_MEDIA_SAIDA, 0) or 0
        media_semanal = media_diaria * 7
        dados.append([
            str(row.get(COL_PRODUTO, "")),
            

            f"{formatar_numero(media_semanal)} g/semana",
            f"{formatar_numero(row.get(COL_ESTOQUE_ATUAL, 0))} g",
            data_fmt,
            str(row.get(COL_STATUS_RUPTURA, "")),
            str(row.get(COL_PRIORIDADE_COMPRA, "")),
        ])

    tabela = Table(
        dados,
        colWidths=[200, 100, 95, 100, 170, 120],
        repeatRows=1
    )

    estilo_tabela = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D5DB")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]

    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        estilo_tabela.append(
            ("BACKGROUND", (0, idx), (-1, idx), cor_prioridade(row.get(COL_PRIORIDADE_COMPRA, "")))
        )

    tabela.setStyle(TableStyle(estilo_tabela))
    elementos.append(tabela)

    # Rodapé
    elementos.append(Spacer(1, 18))
    elementos.append(Paragraph(
        f"Relatório gerado por {NOME_EMPRESA} • Inteligência de dados para tomada de decisão",
        rodape_style
    ))

    doc.build(elementos)


# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":
    df_relatorios = carregar_dados_relatorios()
    df_final = preparar_relatorio(df_relatorios)

    nome_arquivo = f"Relatorio_Ruptura_{NOME_CLIENTE.replace(' ', '_')}_{datetime.now().strftime('%d-%m-%Y_%H-%M')}.pdf"
    gerar_pdf_relatorio_ruptura(df_final, nome_arquivo)

    print(f"PDF gerado com sucesso: {nome_arquivo}")