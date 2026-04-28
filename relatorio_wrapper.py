import sys
import os
import traceback
import tkinter as tk
from tkinter import messagebox
from datetime import datetime


def mostrar_popup(titulo: str, mensagem: str, erro: bool = False):
    root = tk.Tk()
    root.withdraw()
    if erro:
        messagebox.showerror(titulo, mensagem)
    else:
        messagebox.showinfo(titulo, mensagem)
    root.destroy()


def main():
    try:
        import relatorio as rel

        df_relatorios = rel.carregar_dados_relatorios()
        df_final = rel.preparar_relatorio(df_relatorios)

        nome_arquivo = (
            f"Relatorio_Ruptura_"
            f"{rel.NOME_CLIENTE.replace(' ', '_')}_"
            f"{datetime.now().strftime('%d-%m-%Y_%H-%M')}.pdf"
        )

        # Salva na mesma pasta do executável (ou do script em modo dev)
        if getattr(sys, "frozen", False):
            pasta_saida = os.path.dirname(sys.executable)
        else:
            pasta_saida = os.path.dirname(os.path.abspath(__file__))

        caminho_completo = os.path.join(pasta_saida, nome_arquivo)

        rel.gerar_pdf_relatorio_ruptura(df_final, caminho_completo)

        mostrar_popup(
            "Relatório Gerado com Sucesso",
            f"PDF salvo em:\n\n{caminho_completo}",
        )

    except Exception:
        erro = traceback.format_exc()
        mostrar_popup(
            "Erro ao Gerar Relatório",
            f"Ocorreu um erro:\n\n{erro}",
            erro=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
