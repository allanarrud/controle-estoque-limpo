import sys
import traceback
import tkinter as tk
from tkinter import messagebox


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
        import main as bot
        print("Bot de alertas iniciado. Pressione Ctrl+C para parar.")
        bot.main()
    except KeyboardInterrupt:
        mostrar_popup("Bot encerrado", "Bot de alertas encerrado pelo usuário.")
    except Exception:
        erro = traceback.format_exc()
        mostrar_popup(
            "Erro no Bot de Alertas",
            f"Ocorreu um erro ao iniciar o bot:\n\n{erro}",
            erro=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
