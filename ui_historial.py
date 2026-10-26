import customtkinter as ctk
from tkinter import ttk, messagebox
import os
import database

class HistorialModule(ctk.CTkFrame):
    def __init__(self, master, app_parent):
        super().__init__(master, fg_color="transparent")
        self.app_parent = app_parent
        self.setup_ui()

    def setup_ui(self):
        f_top = ctk.CTkFrame(self, fg_color="transparent")
        f_top.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(f_top, text="🧾 REGISTRO HISTÓRICO DE VENTAS Y TICKETS", font=("Roboto", 18, "bold")).pack(side="left")
        ctk.CTkButton(f_top, text="📄 Ver Ticket Seleccionado", command=self.ver_ticket).pack(side="right", padx=5)

        self.tabla = ttk.Treeview(self, columns=("ID", "FECHA", "USD", "BS", "TASA", "METODO", "TURNO"), show="headings")
        for col, tit, anc in [
            ("ID", "TICKET #", 80), ("FECHA", "FECHA Y HORA", 150), ("USD", "TOTAL $", 90),
            ("BS", "TOTAL BS", 110), ("TASA", "TASA BCV", 90), ("METODO", "MÉTODO DE PAGO", 220), ("TURNO", "ESTADO CORTE", 120)
        ]:
            self.tabla.heading(col, text=tit)
            self.tabla.column(col, width=anc, anchor="center")
        self.tabla.pack(fill="both", expand=True, padx=20, pady=10)

    def cargar_ventas(self):
        for i in self.tabla.get_children():
            self.tabla.delete(i)
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("SELECT id, fecha, total_usd, total_bs, tasa_aplicada, metodo_pago, IFNULL(caja_sesion_id, 0) FROM Ventas ORDER BY id DESC LIMIT 200")
        for v in c.fetchall():
            estado_turno = "🟢 Turno Abierto" if v[6] == 0 else f"🔒 Corte #{v[6]:04d}"
            self.tabla.insert("", "end", values=(
                f"{v[0]:06d}", v[1], f"${v[2]:.2f}", f"Bs. {v[3]:.2f}", v[4], v[5], estado_turno
            ))
        conn.close()

    def ver_ticket(self):
        sel = self.tabla.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Seleccione una venta de la tabla.")
        venta_id = int(self.tabla.item(sel[0])['values'][0])
        ruta = os.path.join("Tickets", f"Ticket_{venta_id}.txt")
        if os.path.exists(ruta):
            os.startfile(ruta)
        else:
            messagebox.showinfo("Ticket", f"El archivo físico {ruta} no se encuentra en la carpeta.")