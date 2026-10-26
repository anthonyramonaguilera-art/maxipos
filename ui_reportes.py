import customtkinter as ctk
from tkinter import ttk, messagebox
import database
from controlador_reportes import ReportesController

class ReportesModule(ctk.CTkFrame):
    def __init__(self, master, app_parent):
        super().__init__(master, fg_color="transparent")
        self.app_parent = app_parent
        self.setup_ui()

    def setup_ui(self):
        f_header = ctk.CTkFrame(self, fg_color="transparent")
        f_header.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(f_header, text="📊 PANEL FINANCIERO Y CIERRE DE CAJA (CORTE Z)", font=("Roboto", 18, "bold")).pack(side="left")

        ctk.CTkButton(
            f_header, text="🔒 REALIZAR CORTE Z (REINICIAR TURNO A $0.00)",
            fg_color="#e74c3c", hover_color="#c0392b", height=40, font=("Roboto", 13, "bold"),
            command=self.hacer_corte_z
        ).pack(side="right", padx=5)

        f_cards = ctk.CTkFrame(self, fg_color="transparent")
        f_cards.pack(fill="x", padx=20, pady=10)
        for i in range(4):
            f_cards.grid_columnconfigure(i, weight=1)

        self.card_turno = self.crear_tarjeta(f_cards, 0, "🟢 TURNO ACTUAL (SIN CERRAR)", "#2ecc71")
        self.card_hoy = self.crear_tarjeta(f_cards, 1, "📅 TOTAL VENTAS DE HOY", "#3498db")
        self.card_ayer = self.crear_tarjeta(f_cards, 2, "⏪ VENTAS DE AYER", "#f39c12")
        self.card_mes = self.crear_tarjeta(f_cards, 3, "🗓️ ACUMULADO DEL MES", "#9b59b6")

        ctk.CTkLabel(self, text="📜 HISTORIAL DE CORTES Z CERRADOS", font=("Roboto", 14, "bold")).pack(anchor="w", padx=25, pady=(15, 5))

        f_tabla = ctk.CTkFrame(self, fg_color="transparent")
        f_tabla.pack(fill="both", expand=True, padx=20, pady=5)

        self.tabla_cortes = ttk.Treeview(f_tabla, columns=("ID", "FECHA", "CANT", "USD", "BS", "GAN", "DESGLOSE"), show="headings")
        for col, tit, anc in [
            ("ID", "CORTE #", 65), ("FECHA", "FECHA Y HORA", 145), ("CANT", "VENTAS", 65),
            ("USD", "TOTAL $", 90), ("BS", "TOTAL BS", 110), ("GAN", "GANANCIA $", 95), ("DESGLOSE", "DESGLOSE DE PAGOS", 320)
        ]:
            self.tabla_cortes.heading(col, text=tit)
            self.tabla_cortes.column(col, width=anc, anchor="center")
        self.tabla_cortes.pack(fill="both", expand=True)

    def crear_tarjeta(self, parent, col, titulo, color):
        frame = ctk.CTkFrame(parent, corner_radius=10, border_width=2, border_color=color)
        frame.grid(row=0, column=col, padx=6, pady=5, sticky="nsew")
        ctk.CTkLabel(frame, text=titulo, font=("Roboto", 11, "bold"), text_color=color).pack(pady=(10, 4))
        lbl_usd = ctk.CTkLabel(frame, text="$0.00", font=("Roboto", 22, "bold"))
        lbl_usd.pack()
        lbl_bs = ctk.CTkLabel(frame, text="Bs. 0.00", font=("Roboto", 13))
        lbl_bs.pack()
        lbl_extra = ctk.CTkLabel(frame, text="0 ventas", font=("Roboto", 11), text_color="gray")
        lbl_extra.pack(pady=(2, 10))
        return (lbl_usd, lbl_bs, lbl_extra)

    def cargar_datos(self):
        res = ReportesController.obtener_resumen_periodos()

        t = res['turno']
        self.card_turno[0].configure(text=f"${t['usd']:.2f}")
        self.card_turno[1].configure(text=f"Bs. {t['bs']:.2f}")
        self.card_turno[2].configure(text=f"{t['cant']} ventas | Ganancia: +${t['ganancia']:.2f}")

        for llave, card in [('hoy', self.card_hoy), ('ayer', self.card_ayer), ('mes', self.card_mes)]:
            d = res[llave]
            card[0].configure(text=f"${d['usd']:.2f}")
            card[1].configure(text=f"Bs. {d['bs']:.2f}")
            card[2].configure(text=f"{d['cant']} operaciones registradas")

        for i in self.tabla_cortes.get_children():
            self.tabla_cortes.delete(i)
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("SELECT id, fecha_corte, total_ventas, total_usd, total_bs, ganancia_usd, desglose_pagos FROM Cortes_Z ORDER BY id DESC LIMIT 60")
        for r in c.fetchall():
            self.tabla_cortes.insert("", "end", values=(
                f"#{r[0]:04d}", r[1], r[2], f"${r[3]:.2f}", f"Bs. {r[4]:.2f}", f"+${r[5]:.2f}", r[6]
            ))
        conn.close()

    def hacer_corte_z(self):
        if messagebox.askyesno("Confirmar Cierre de Turno (Corte Z)", "¿Desea cerrar el turno actual, enviar el reporte a Telegram y reiniciar la caja a $0.00?"):
            ok, msg = ReportesController.ejecutar_corte_z(self.app_parent.tasa_actual, es_automatico=False)
            if ok:
                messagebox.showinfo("Corte Z Exitoso", msg)
            else:
                messagebox.showwarning("Aviso de Corte Z", msg)
            self.cargar_datos()