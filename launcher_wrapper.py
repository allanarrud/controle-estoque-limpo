"""
Entry point para o PyInstaller.
Captura qualquer erro de inicialização antes de abrir a janela.
"""
import sys
import traceback


def main():
    try:
        from app_launcher import GmdcApp
        app = GmdcApp()
        app.mainloop()
    except Exception:
        import tkinter as tk
        from tkinter import messagebox
        err = traceback.format_exc()
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("GM DataCore — Erro Fatal", err)
        root.destroy()
        sys.exit(1)


if __name__ == "__main__":
    main()
