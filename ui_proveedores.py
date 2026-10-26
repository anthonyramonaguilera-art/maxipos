import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
import database

class ProveedoresModule(ctk.CTkFrame):
    def __init__(self, master, app_parent):
        super().__init__(master, fg_color="transparent")
        self.app_parent = app_parent
        self.vcmd_num = (self.register(self.validar_numero), '%P')
        self.setup_ui()

    def validar_numero(self, texto):
        if texto == "":
            return True
        norm = texto.replace(',', '.')
        if norm.count('.') > 1:
            return False
        for p in norm.split('.'):
            if p != "" and not p.isdigit():
                return False
        return True

    def setup_ui(self):
        f_sup = ctk.CTkFrame(self)
        f_sup.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(f_sup, text="🚚 REGISTRAR PROVEEDOR", font=("Roboto", 14, "bold")).grid(row=0, column=0, columnspan=4, pady=6, padx=10, sticky="w")
        self.e_rif = ctk.CTkEntry(f_sup, placeholder_text="RIF / Documento", width=140)
        self.e_rif.grid(row=1, column=0, padx=6, pady=6)
        self.e_nom = ctk.CTkEntry(f_sup, placeholder_text="Nombre Contacto", width=180)
        self.e_nom.grid(row=1, column=1, padx=6, pady=6)
        self.e_tel = ctk.CTkEntry(f_sup, placeholder_text="Teléfono", width=140)
        self.e_tel.grid(row=1, column=2, padx=6, pady=6)
        self.e_emp = ctk.CTkEntry(f_sup, placeholder_text="Empresa / Marca", width=180)
        self.e_emp.grid(row=1, column=3, padx=6, pady=6)
        ctk.CTkButton(f_sup, text="➕ Guardar Proveedor", fg_color="#2ecc71", command=self.guardar_prov).grid(row=1, column=4, padx=10, pady=6)

        f_deu = ctk.CTkFrame(self)
        f_deu.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(f_deu, text="📑 REGISTRAR FACTURA / CUENTA POR PAGAR", font=("Roboto", 14, "bold")).grid(row=0, column=0, columnspan=4, pady=6, padx=10, sticky="w")
        self.cb_prov = ctk.CTkComboBox(f_deu, values=["Seleccione..."], width=200)
        self.cb_prov.grid(row=1, column=0, padx=6, pady=6)
        self.e_desc = ctk.CTkEntry(f_deu, placeholder_text="Descripción / Nro Factura", width=200)
        self.e_desc.grid(row=1, column=1, padx=6, pady=6)
        self.e_monto = ctk.CTkEntry(f_deu, placeholder_text="Monto Total $", width=130, validate="key", validatecommand=self.vcmd_num)
        self.e_monto.grid(row=1, column=2, padx=6, pady=6)
        self.e_vence = ctk.CTkEntry(f_deu, placeholder_text="Vence (YYYY-MM-DD)", width=150)
        self.e_vence.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.e_vence.grid(row=1, column=3, padx=6, pady=6)
        ctk.CTkButton(f_deu, text="📌 Registrar Deuda", fg_color="#3498db", command=self.guardar_deuda).grid(row=1, column=4, padx=10, pady=6)

        self.tabla_deudas = ttk.Treeview(self, columns=("ID", "PROV", "DESC", "TOTAL", "ABONADO", "VENCE", "ESTADO"), show="headings")
        for col, tit, anc in [
            ("ID", "ID", 40), ("PROV", "PROVEEDOR", 160), ("DESC", "DESCRIPCIÓN", 200),
            ("TOTAL", "MONTO $", 90), ("ABONADO", "ABONADO $", 90), ("VENCE", "VENCIMIENTO", 110), ("ESTADO", "ESTADO", 100)
        ]:
            self.tabla_deudas.heading(col, text=tit)
            self.tabla_deudas.column(col, width=anc, anchor="center")
        self.tabla_deudas.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkButton(self, text="✅ Marcar Cuenta Seleccionada como PAGADA", fg_color="#27ae60", command=self.pagar_deuda).pack(pady=(0, 10))

    def cargar_provs(self):
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("SELECT id, nombre, empresa FROM Proveedores")
        provs = [f"{r[0]} - {r[1]} ({r[2]})" for r in c.fetchall()]
        conn.close()
        self.cb_prov.configure(values=provs if provs else ["Sin proveedores"])
        if provs:
            self.cb_prov.set(provs[0])

    def cargar_deudas(self):
        for i in self.tabla_deudas.get_children():
            self.tabla_deudas.delete(i)
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("""SELECT cp.id, IFNULL(p.nombre, 'General'), cp.descripcion, cp.monto_total_usd, cp.abonado_usd, cp.fecha_vencimiento, cp.estado
                     FROM Cuentas_Pagar cp LEFT JOIN Proveedores p ON cp.proveedor_id = p.id ORDER BY cp.id DESC""")
        for r in c.fetchall():
            self.tabla_deudas.insert("", "end", values=(r[0], r[1], r[2], f"${r[3]:.2f}", f"${r[4]:.2f}", r[5], r[6]))
        conn.close()

    def guardar_prov(self):
        if not self.e_nom.get().strip():
            return messagebox.showwarning("Aviso", "Ingrese el nombre del proveedor.")
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("INSERT INTO Proveedores (rif, nombre, telefono, empresa) VALUES (?,?,?,?)",
                  (self.e_rif.get().strip(), self.e_nom.get().strip().upper(), self.e_tel.get().strip(), self.e_emp.get().strip().upper()))
        conn.commit()
        conn.close()
        for e in [self.e_rif, self.e_nom, self.e_tel, self.e_emp]:
            e.delete(0, 'end')
        self.cargar_provs()
        messagebox.showinfo("OK", "Proveedor registrado.")

    def guardar_deuda(self):
        sel = self.cb_prov.get()
        if "-" not in sel:
            return messagebox.showwarning("Aviso", "Seleccione un proveedor válido.")
        prov_id = int(sel.split("-")[0].strip())
        try:
            monto = float(self.e_monto.get().replace(',', '.'))
        except Exception:
            return messagebox.showwarning("Aviso", "Ingrese un monto válido.")

        conn = database.conectar_db()
        c = conn.cursor()
        hoy = datetime.now().strftime("%Y-%m-%d")
        c.execute("""INSERT INTO Cuentas_Pagar (proveedor_id, descripcion, monto_total_usd, abonado_usd, fecha_emision, fecha_vencimiento, estado)
                     VALUES (?, ?, ?, 0, ?, ?, 'PENDIENTE')""",
                  (prov_id, self.e_desc.get().strip(), monto, hoy, self.e_vence.get().strip()))
        conn.commit()
        conn.close()
        self.e_desc.delete(0, 'end')
        self.e_monto.delete(0, 'end')
        self.cargar_deudas()

    def pagar_deuda(self):
        sel = self.tabla_deudas.selection()
        if not sel:
            return
        deuda_id = self.tabla_deudas.item(sel[0])['values'][0]
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("UPDATE Cuentas_Pagar SET abonado_usd = monto_total_usd, estado = 'PAGADA' WHERE id = ?", (deuda_id,))
        conn.commit()
        conn.close()
        self.cargar_deudas()