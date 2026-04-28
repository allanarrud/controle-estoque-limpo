import sys
import os
import threading
import traceback
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import font as tkfont

# ── Paleta GM DataCore ──────────────────────────────────────────────────────
BG_DEEP    = "#0A0A0F"
BG_CARD    = "#12121A"
BG_CARD2   = "#161620"
BORDER     = "#2A2A40"
ACCENT1    = "#6C63FF"   # roxo elétrico
ACCENT2    = "#00D4FF"   # ciano
TEXT_PRI   = "#E8E8F0"
TEXT_SEC   = "#7777AA"
TEXT_DIM   = "#44445A"
SUCCESS    = "#22C55E"
ERROR      = "#EF4444"
WARNING    = "#F59E0B"
GLOW_ROXO  = "#6C63FF"
GLOW_CYAN  = "#00D4FF"

# ── Resolve caminho de resource (funciona frozen e dev) ─────────────────────
def resource(rel_path: str) -> str:
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel_path)


# ═══════════════════════════════════════════════════════════════════════════
# WIDGETS CUSTOMIZADOS
# ═══════════════════════════════════════════════════════════════════════════

class GlowButton(tk.Frame):
    """Botão retangular com borda colorida e efeito hover."""

    def __init__(self, parent, text, icon, color, command, **kwargs):
        super().__init__(parent, bg=BG_CARD,
                         highlightbackground=color,
                         highlightthickness=1,
                         cursor="hand2", **kwargs)
        self._color   = color
        self._command = command
        self._running = False

        self._label = tk.Label(self, text=f"{icon}  {text}",
                               font=("Segoe UI Semibold", 11),
                               fg=TEXT_PRI, bg=BG_CARD,
                               padx=20, pady=14)
        self._label.pack()

        for w in (self, self._label):
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)
            w.bind("<Button-1>", self._on_click)

    def _on_enter(self, _):
        self.config(bg=BG_CARD2, highlightbackground=self._color, highlightthickness=2)
        self._label.config(bg=BG_CARD2)

    def _on_leave(self, _):
        self.config(bg=BG_CARD, highlightbackground=self._color, highlightthickness=1)
        self._label.config(bg=BG_CARD)

    def _on_click(self, _):
        if not self._running:
            self._command()

    def set_running(self, state: bool):
        self._running = state
        fg = TEXT_SEC if state else TEXT_PRI
        self._label.config(fg=fg)


class StatusDot(tk.Canvas):
    """Bolinha de status animada."""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", BG_CARD)
        super().__init__(parent, width=10, height=10,
                         highlightthickness=0, **kwargs)
        self._color = TEXT_DIM
        self._draw()

    def _draw(self):
        if not self.winfo_exists():
            return
        self.delete("all")
        self.create_oval(1, 1, 9, 9, fill=self._color, outline="")

    def set_color(self, color: str):
        self._color = color
        self._draw()


# ═══════════════════════════════════════════════════════════════════════════
# JANELA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

class GmdcApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("GM DataCore — Controle de Estoque")
        self.configure(bg=BG_DEEP)
        self.resizable(False, False)

        # tenta carregar logo
        self._logo_img = None
        try:
            from PIL import Image, ImageTk
            img = Image.open(resource(os.path.join("assets", "logo-monte-sinai-cropped.png")))
            img = img.resize((72, 72), Image.LANCZOS)
            self._logo_img = ImageTk.PhotoImage(img)
        except Exception:
            pass

        self._build_ui()
        self._center_window()
        self._log("Sistema pronto.", color=TEXT_SEC)

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Topo: header ────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG_DEEP, pady=24)
        header.pack(fill="x", padx=32)

        left = tk.Frame(header, bg=BG_DEEP)
        left.pack(side="left")

        if self._logo_img:
            tk.Label(left, image=self._logo_img, bg=BG_DEEP).pack(side="left", padx=(0, 16))

        titles = tk.Frame(left, bg=BG_DEEP)
        titles.pack(side="left")
        tk.Label(titles, text="Monte Sinai Ervas",
                 font=("Segoe UI", 18, "bold"),
                 fg=TEXT_PRI, bg=BG_DEEP).pack(anchor="w")
        tk.Label(titles, text="Plataforma de Gestão de Estoque",
                 font=("Segoe UI", 10),
                 fg=TEXT_SEC, bg=BG_DEEP).pack(anchor="w")

        # badge GM DataCore
        badge = tk.Frame(header, bg=BG_DEEP)
        badge.pack(side="right", anchor="ne")
        tk.Label(badge, text="GM DataCore",
                 font=("Segoe UI", 8, "bold"),
                 fg=ACCENT1, bg=BG_DEEP).pack(anchor="e")
        tk.Label(badge, text="Inteligência de dados",
                 font=("Segoe UI", 8),
                 fg=TEXT_DIM, bg=BG_DEEP).pack(anchor="e")

        # ── Divisor ─────────────────────────────────────────────────────────
        self._divider(BG_DEEP)

        # ── Cards ───────────────────────────────────────────────────────────
        cards_frame = tk.Frame(self, bg=BG_DEEP, padx=28, pady=20)
        cards_frame.pack(fill="x")

        self._card_relatorio = self._build_card(
            parent   = cards_frame,
            side     = "left",
            icon     = "📄",
            title    = "Relatório de Ruptura",
            desc     = "Gera PDF executivo com análise\nde ruptura, prioridades e prazos.",
            color    = ACCENT1,
            btn_text = "Gerar Relatório",
            btn_icon = "⚡",
            command  = self._run_relatorio,
        )

        tk.Frame(cards_frame, bg=BG_DEEP, width=16).pack(side="left")

        self._card_alerta = self._build_card(
            parent   = cards_frame,
            side     = "left",
            icon     = "🤖",
            title    = "Bot de Alertas",
            desc     = "Inicia o bot do Telegram com\nalertas automáticos de estoque.",
            color    = ACCENT2,
            btn_text = "Enviar Alertas",
            btn_icon = "📡",
            command  = self._run_alerta,
        )

        # ── Divisor ─────────────────────────────────────────────────────────
        self._divider(BG_DEEP)

        # ── Barra de log ────────────────────────────────────────────────────
        log_frame = tk.Frame(self, bg=BG_CARD, padx=20, pady=12)
        log_frame.pack(fill="x", side="bottom")

        top_row = tk.Frame(log_frame, bg=BG_CARD)
        top_row.pack(fill="x")

        tk.Label(top_row, text="LOG DO SISTEMA",
                 font=("Segoe UI", 7, "bold"),
                 fg=TEXT_DIM, bg=BG_CARD).pack(side="left")

        self._status_dot = StatusDot(top_row, bg=BG_CARD)
        self._status_dot.pack(side="right", padx=(0, 4))

        self._log_var = tk.StringVar(value="")
        tk.Label(log_frame, textvariable=self._log_var,
                 font=("Consolas", 9),
                 fg=TEXT_SEC, bg=BG_CARD,
                 anchor="w", justify="left",
                 wraplength=480).pack(fill="x", pady=(6, 0))

        # ── Rodapé ──────────────────────────────────────────────────────────
        footer = tk.Frame(self, bg=BG_DEEP, pady=8)
        footer.pack(fill="x")
        now = datetime.now().strftime("%d/%m/%Y")
        tk.Label(footer,
                 text=f"© {datetime.now().year} GM DataCore  •  {now}",
                 font=("Segoe UI", 8),
                 fg=TEXT_DIM, bg=BG_DEEP).pack()

    def _divider(self, bg):
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28)

    def _build_card(self, parent, side, icon, title, desc, color, btn_text, btn_icon, command):
        card = tk.Frame(parent, bg=BG_CARD,
                        padx=24, pady=20,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(side=side, fill="both", expand=True)

        # ícone grande
        tk.Label(card, text=icon,
                 font=("Segoe UI Emoji", 32),
                 fg=color, bg=BG_CARD).pack(anchor="w")

        tk.Frame(card, bg=BG_CARD, height=8).pack()

        # título
        tk.Label(card, text=title,
                 font=("Segoe UI", 13, "bold"),
                 fg=TEXT_PRI, bg=BG_CARD).pack(anchor="w")

        # descrição
        tk.Label(card, text=desc,
                 font=("Segoe UI", 9),
                 fg=TEXT_SEC, bg=BG_CARD,
                 justify="left").pack(anchor="w", pady=(4, 16))

        # botão
        btn = GlowButton(card, text=btn_text, icon=btn_icon,
                         color=color, command=command)
        btn.pack(anchor="w")

        return {"frame": card, "btn": btn}

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── Log ─────────────────────────────────────────────────────────────────

    def _log(self, msg: str, color: str = TEXT_SEC):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_var.set(f"[{ts}]  {msg}")
        self._status_dot.set_color(color)

    # ── Ações ────────────────────────────────────────────────────────────────

    def _run_relatorio(self):
        btn = self._card_relatorio["btn"]
        btn.set_running(True)
        self._log("Gerando relatório PDF...", color=WARNING)

        def worker():
            try:
                import relatorio as rel
                from datetime import datetime as dt

                df = rel.carregar_dados_relatorios()
                df_final = rel.preparar_relatorio(df)

                nome = (
                    f"Relatorio_Ruptura_"
                    f"{rel.NOME_CLIENTE.replace(' ', '_')}_"
                    f"{dt.now().strftime('%d-%m-%Y_%H-%M')}.pdf"
                )

                if getattr(sys, "frozen", False):
                    pasta = os.path.dirname(sys.executable)
                else:
                    pasta = os.path.dirname(os.path.abspath(__file__))

                caminho = os.path.join(pasta, nome)
                rel.gerar_pdf_relatorio_ruptura(df_final, caminho)

                self.after(0, lambda: self._log(f"PDF gerado: {nome}", color=SUCCESS))
                self.after(0, lambda: self._show_toast("Relatório gerado!", caminho, ok=True))
            except Exception:
                err = traceback.format_exc().strip().splitlines()[-1]
                self.after(0, lambda: self._log(f"Erro: {err}", color=ERROR))
                self.after(0, lambda: self._show_toast("Erro ao gerar relatório", err, ok=False))
            finally:
                self.after(0, lambda: btn.set_running(False))

        threading.Thread(target=worker, daemon=True).start()

    def _run_alerta(self):
        btn = self._card_alerta["btn"]
        btn.set_running(True)
        self._log("Iniciando bot de alertas...", color=WARNING)

        def worker():
            try:
                import main as bot
                self.after(0, lambda: self._log("Bot Telegram rodando.", color=SUCCESS))
                bot.main()
                self.after(0, lambda: self._log("Bot encerrado.", color=TEXT_SEC))
            except Exception:
                err = traceback.format_exc().strip().splitlines()[-1]
                self.after(0, lambda: self._log(f"Erro no bot: {err}", color=ERROR))
                self.after(0, lambda: self._show_toast("Erro no bot de alertas", err, ok=False))
            finally:
                self.after(0, lambda: btn.set_running(False))

        threading.Thread(target=worker, daemon=True).start()

    # ── Toast popup ─────────────────────────────────────────────────────────

    def _show_toast(self, title: str, detail: str, ok: bool):
        color  = SUCCESS if ok else ERROR
        icon   = "✅" if ok else "❌"

        popup = tk.Toplevel(self)
        popup.title("")
        popup.configure(bg=BG_CARD)
        popup.resizable(False, False)
        popup.grab_set()

        frame = tk.Frame(popup, bg=BG_CARD, padx=28, pady=24)
        frame.pack()

        tk.Label(frame, text=f"{icon}  {title}",
                 font=("Segoe UI", 12, "bold"),
                 fg=color, bg=BG_CARD).pack(anchor="w")

        tk.Frame(frame, bg=BORDER, height=1).pack(fill="x", pady=10)

        tk.Label(frame, text=detail,
                 font=("Consolas", 9),
                 fg=TEXT_SEC, bg=BG_CARD,
                 wraplength=380, justify="left").pack(anchor="w")

        tk.Frame(frame, bg=BG_CARD, height=12).pack()

        close_btn = tk.Button(
            frame, text="Fechar",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_PRI, bg=color,
            activebackground=color,
            activeforeground=TEXT_PRI,
            relief="flat", cursor="hand2",
            padx=20, pady=6,
            command=popup.destroy,
        )
        close_btn.pack(anchor="e")

        # centraliza sobre a janela principal
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - popup.winfo_width())  // 2
        y = self.winfo_y() + (self.winfo_height() - popup.winfo_height()) // 2
        popup.geometry(f"+{x}+{y}")


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = GmdcApp()
    app.mainloop()
