import customtkinter as ctk
from tkinter import ttk, messagebox
import os
import database
from controlador_reportes import ReportesController

class ReportesModule(ctk.CTkFrame):
    def __init__(self, master, app_parent):
        super().__init__(master, fg_color="transparent")
        self.app_parent = app_parent
        self.setup_ui()

    def setup_ui(self):
        f_header = ctk.CTkFrame(self, fg_color="transparent")
        f_header.pack(fill="x", padx=18, pady=(8, 4))

        ctk.CTkLabel(f_header, text="📊 CONTABILIDAD INTELIGENTE Y CORTE DE CAJA (Z)", font=("Roboto", 19, "bold")).pack(side="left")

        ctk.CTkButton(
            f_header, text="🔒 CERRAR TURNO / CORTE Z (REINICIAR A $0.00)",
            fg_color="#e74c3c", hover_color="#c0392b", height=40, font=("Roboto", 13, "bold"),
            command=self.hacer_corte_z
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            f_header, text="📄 Abrir Reporte Seleccionado",
            fg_color="#34495e", height=40, font=("Roboto", 12, "bold"),
            command=self.abrir_txt_corte
        ).pack(side="right", padx=5)

        # FILA 1: 4 Tarjetas Temporales (Turno Abierto, Hoy, Ayer, Mes)
        f_cards = ctk.CTkFrame(self, fg_color="transparent")
        f_cards.pack(fill="x", padx=18, pady=4)
        for i in range(4):
            f_cards.grid_columnconfigure(i, weight=1)

        self.card_turno = self.crear_tarjeta(f_cards, 0, "🟢 TURNO ACTUAL (ABIERTO)", "#2ecc71")
        self.card_hoy = self.crear_tarjeta(f_cards, 1, "📅 VENTAS DE HOY", "#3498db")
        self.card_ayer = self.crear_tarjeta(f_cards, 2, "⏪ VENTAS DE AYER", "#f39c12")
        self.card_mes = self.crear_tarjeta(f_cards, 3, "🗓️ ACUMULADO DEL MES", "#9b59b6")

        # FILA 2: Paneles Inteligentes de Contabilidad (Capital vs Ganancia, Arqueo de Pagos, Inteligencia de Stock)
        f_intel = ctk.CTkFrame(self, fg_color="transparent")
        f_intel.pack(fill="x", padx=18, pady=6)
        for i in range(3):
            f_intel.grid_columnconfigure(i, weight=1)

        # Panel 1: Contabilidad del Turno (Capital a Reponer vs Ganancia Neta)
        p_cont = ctk.CTkFrame(f_intel, corner_radius=10, border_width=1, border_color="#34495e")
        p_cont.grid(row=0, column=0, padx=5, sticky="nsew")
        ctk.CTkLabel(p_cont, text="💰 CONTABILIDAD DEL TURNO ACTUAL", font=("Roboto", 13, "bold"), text_color="#f1c40f").pack(pady=(8, 4))
        self.lbl_inicio_turno = ctk.CTkLabel(p_cont, text="Inicio Turno: --", font=("Roboto", 12, "bold"))
        self.lbl_inicio_turno.pack(pady=2)
        self.lbl_capital = ctk.CTkLabel(p_cont, text="📦 Capital a Reponer (Costo): $0.00", font=("Roboto", 13, "bold"), text_color="#e67e22")
        self.lbl_capital.pack(pady=2)
        self.lbl_ganancia = ctk.CTkLabel(p_cont, text="📈 Ganancia Neta Libre: +$0.00", font=("Roboto", 14, "bold"), text_color="#2ecc71")
        self.lbl_ganancia.pack(pady=(2, 8))

        # Panel 2: Arqueo de Caja por Método de Pago
        p_arq = ctk.CTkFrame(f_intel, corner_radius=10, border_width=1, border_color="#34495e")
        p_arq.grid(row=0, column=1, padx=5, sticky="nsew")
        ctk.CTkLabel(p_arq, text="💳 DINERO EN CAJA (TURNO ACTUAL)", font=("Roboto", 13, "bold"), text_color="#3498db").pack(pady=(8, 4))
        self.lbl_arq_efec = ctk.CTkLabel(p_arq, text="💵 Efectivo ($): $0.00", font=("Roboto", 13, "bold"))
        self.lbl_arq_efec.pack(pady=2)
        self.lbl_arq_punto = ctk.CTkLabel(p_arq, text="💳 Punto de Venta (Bs): Bs. 0.00", font=("Roboto", 13, "bold"))
        self.lbl_arq_punto.pack(pady=2)
        self.lbl_arq_pm = ctk.CTkLabel(p_arq, text="📱 Pago Móvil (Bs): Bs. 0.00", font=("Roboto", 13, "bold"))
        self.lbl_arq_pm.pack(pady=(2, 8))

        # Panel 3: Inteligencia de Inventario y Más Vendidos
        p_top = ctk.CTkFrame(f_intel, corner_radius=10, border_width=1, border_color="#34495e")
        p_top.grid(row=0, column=2, padx=5, sticky="nsew")
        ctk.CTkLabel(p_top, text="🏆 TOP VENTAS Y ALERTAS DE STOCK", font=("Roboto", 13, "bold"), text_color="#e74c3c").pack(pady=(8, 4))
        self.lbl_top_prod = ctk.CTkLabel(p_top, text="Más vendidos: Sin datos", font=("Roboto", 12, "bold"), justify="left")
        self.lbl_top_prod.pack(pady=2, padx=8)
        self.lbl_alerta_stock = ctk.CTkLabel(p_top, text="Stock Crítico: Todo en orden", font=("Roboto", 12, "bold"), text_color="#e67e22", justify="left")
        self.lbl_alerta_stock.pack(pady=(2, 8), padx=8)

        # Tabla Histórica de Cortes Z con Hora de Inicio y Hora de Fin
        ctk.CTkLabel(self, text="📜 HISTORIAL DE CORTES Z CERRADOS (CON HORA DE INICIO Y CIERRE EN LA NUBE)", font=("Roboto", 13, "bold")).pack(anchor="w", padx=22, pady=(6, 2))

        f_tabla = ctk.CTkFrame(self, fg_color="transparent")
        f_tabla.pack(fill="both", expand=True, padx=18, pady=4)

        self.tabla_cortes = ttk.Treeview(
            f_tabla,
            columns=("ID", "INICIO", "CIERRE", "CANT", "USD", "COSTO", "GAN", "BS", "DESGLOSE"),
            show="headings"
        )
        for col, tit, anc in [
            ("ID", "CORTE #", 65),
            ("INICIO", "HORA INICIO", 135),
            ("CIERRE", "HORA CIERRE", 135),
            ("CANT", "VENTAS", 60),
            ("USD", "BRUTO $", 80),
            ("COSTO", "COSTO $", 80),
            ("GAN", "GANANCIA $", 90),
            ("BS", "TOTAL BS", 105),
            ("DESGLOSE", "DESGLOSE DE PAGOS", 260)
        ]:
            self.tabla_cortes.heading(col, text=tit)
            self.tabla_cortes.column(col, width=anc, anchor="center")
        self.tabla_cortes.pack(fill="both", expand=True)

    def crear_tarjeta(self, parent, col, titulo, color):
        frame = ctk.CTkFrame(parent, corner_radius=10, border_width=2, border_color=color)
        frame.grid(row=0, column=col, padx=5, pady=4, sticky="nsew")
        ctk.CTkLabel(frame, text=titulo, font=("Roboto", 12, "bold"), text_color=color).pack(pady=(8, 2))
        lbl_usd = ctk.CTkLabel(frame, text="$0.00", font=("Roboto", 22, "bold"))
        lbl_usd.pack()
        lbl_bs = ctk.CTkLabel(frame, text="Bs. 0.00", font=("Roboto", 13, "bold"))
        lbl_bs.pack()
        lbl_extra = ctk.CTkLabel(frame, text="0 ventas", font=("Roboto", 11, "bold"), text_color="gray")
        lbl_extra.pack(pady=(2, 8))
        return (lbl_usd, lbl_bs, lbl_extra)

    def cargar_datos(self):
        res = ReportesController.obtener_resumen_completo()
        tasa = self.app_parent.tasa_actual

        # Tarjeta Turno
        t = res['turno']
        self.card_turno[0].configure(text=f"${t['usd']:.2f}")
        self.card_turno[1].configure(text=f"Bs. {t['bs']:.2f}")
        self.card_turno[2].configure(text=f"{t['cant']} ventas en turno actual")

        # Tarjetas Hoy, Ayer, Mes
        for llave, card in [('hoy', self.card_hoy), ('ayer', self.card_ayer)]:
            d = res[llave]
            card[0].configure(text=f"${d['usd']:.2f}")
            card[1].configure(text=f"Bs. {d['bs']:.2f}")
            card[2].configure(text=f"{d['cant']} operaciones")

        m = res['mes']
        self.card_mes[0].configure(text=f"${m['usd']:.2f}")
        self.card_mes[1].configure(text=f"Bs. {m['bs']:.2f}")
        self.card_mes[2].configure(text=f"{m['cant']} ventas | Ganancia Mes: +${m['ganancia']:.2f}")

        # Paneles Contables del Turno
        self.lbl_inicio_turno.configure(text=f"🟢 Inicio de Turno: {t['inicio']}")
        self.lbl_capital.configure(text=f"📦 Capital a Reponer: ${t['costo']:.2f} (Bs. {t['costo']*tasa:.2f})")
        self.lbl_ganancia.configure(text=f"📈 Ganancia Neta Libre: +${t['ganancia']:.2f} (Bs. {t['ganancia']*tasa:.2f})")

        self.lbl_arq_efec.configure(text=f"💵 Efectivo ($): ${t['efec_usd']:.2f}")
        self.lbl_arq_punto.configure(text=f"💳 Punto de Venta: Bs. {t['punto_bs']:.2f}")
        self.lbl_arq_pm.configure(text=f"📱 Pago Móvil: Bs. {t['pm_bs']:.2f}")

        # Top Productos y Alertas de Stock
        tops = res['top_productos']
        if tops:
            txt_top = "🔥 Más Vendidos: " + " | ".join([f"{p[0][:12]} (${p[2]:.0f})" for p in tops[:3]])
        else:
            txt_top = "🔥 Más Vendidos: Sin ventas aún"
        self.lbl_top_prod.configure(text=txt_top)

        criticos = res['stock_critico']
        if criticos:
            txt_crit = "⚠️ Por Agotarse: " + ", ".join([f"{c[0][:12]} ({c[1]:g}{c[2][:2]})" for c in criticos[:3]])
        else:
            txt_crit = "✅ Inventario Óptimo (Sin productos en alerta)"
        self.lbl_alerta_stock.configure(text=txt_crit)

        # Tabla Cortes Z
        for i in self.tabla_cortes.get_children():
            self.tabla_cortes.delete(i)
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("""SELECT id, IFNULL(fecha_inicio, fecha_corte), fecha_corte, total_ventas, 
                            total_usd, IFNULL(costo_usd, 0), ganancia_usd, total_bs, desglose_pagos 
                     FROM Cortes_Z ORDER BY id DESC LIMIT 60""")
        for r in c.fetchall():
            self.tabla_cortes.insert("", "end", values=(
                f"#{r[0]:04d}", r[1] or r[2], r[2], r[3],
                f"${r[4]:.2f}", f"${r[5]:.2f}", f"+${r[6]:.2f}", f"Bs. {r[7]:.2f}", r[8]
            ))
        conn.close()

    def hacer_corte_z(self):
        if messagebox.askyesno("Confirmar Cierre de Turno (Corte Z)", "¿Desea cerrar el turno actual y reiniciar la caja a $0.00?"):
            ok, msg = ReportesController.ejecutar_corte_z(self.app_parent.tasa_actual, es_automatico=False)
            if ok:
                messagebox.showinfo("Corte Z Exitoso", msg)
            else:
                messagebox.showwarning("Aviso de Corte Z", msg)
            self.cargar_datos()

    def abrir_txt_corte(self):
        sel = self.tabla_cortes.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Seleccione un Corte Z de la tabla.")
        corte_num = int(str(self.tabla_cortes.item(sel[0])['values'][0]).replace("#", ""))
        ruta = os.path.join("Reportes", f"Corte_Z_{corte_num:04d}.txt")
        if os.path.exists(ruta):
            os.startfile(ruta)
        else:
            messagebox.showinfo("Reporte", f"Archivo no encontrado: {ruta}")