import customtkinter as ctk
from tkinter import ttk, messagebox
import database
from controlador_ventas import VentasController

class CajaModule(ctk.CTkFrame):
    def __init__(self, master, app_parent):
        super().__init__(master, fg_color="transparent")
        self.app_parent = app_parent
        self.carrito = []
        self.modo_mayor = False
        self.vcmd_num = (self.register(self.validar_numero), '%P')
        self.setup_ui()

    def validar_numero(self, texto):
        if texto == "":
            return True
        norm = texto.replace(',', '.')
        if norm.count('.') > 1:
            return False
        for parte in norm.split('.'):
            if parte != "" and not parte.isdigit():
                return False
        return True

    def setup_ui(self):
        f_top = ctk.CTkFrame(self, fg_color="transparent")
        f_top.pack(fill="x", padx=15, pady=(10, 5))

        self.ent_buscar = ctk.CTkEntry(
            f_top,
            placeholder_text="🔍 Escanee código de barras o escriba el nombre del producto (Enter para agregar)...",
            width=480,
            height=40,
            font=("Roboto", 14)
        )
        self.ent_buscar.pack(side="left", padx=(0, 10))
        self.ent_buscar.bind("<KeyRelease>", self.filtrar_catalogo)
        self.ent_buscar.bind("<Return>", self.agregar_primer_resultado)

        ctk.CTkLabel(f_top, text="Cant:", font=("Roboto", 13, "bold")).pack(side="left", padx=4)
        self.ent_cant = ctk.CTkEntry(f_top, width=70, height=40, font=("Roboto", 14, "bold"), validate="key", validatecommand=self.vcmd_num)
        self.ent_cant.insert(0, "1")
        self.ent_cant.pack(side="left", padx=4)

        self.sw_mayor = ctk.CTkSwitch(f_top, text="Precio al Mayor", command=self.toggle_mayor, font=("Roboto", 12, "bold"))
        self.sw_mayor.pack(side="left", padx=12)

        self.lbl_toast = ctk.CTkLabel(f_top, text="", font=("Roboto", 13, "bold"), text_color="#2ecc71")
        self.lbl_toast.pack(side="right", padx=10)

        f_body = ctk.CTkFrame(self, fg_color="transparent")
        f_body.pack(fill="both", expand=True, padx=15, pady=5)
        f_body.grid_columnconfigure(0, weight=5)
        f_body.grid_columnconfigure(1, weight=5)
        f_body.grid_rowconfigure(0, weight=1)

        f_cat = ctk.CTkFrame(f_body)
        f_cat.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=5)

        ctk.CTkLabel(f_cat, text="📦 CATÁLOGO DISPONIBLE (Doble clic para añadir)", font=("Roboto", 13, "bold")).pack(pady=6)

        self.tabla_cat = ttk.Treeview(f_cat, columns=("ID", "COD", "NOM", "USD", "BS", "STOCK"), show="headings")
        for col, tit, anc in [("ID", "ID", 35), ("COD", "CÓDIGO", 75), ("NOM", "PRODUCTO", 180), ("USD", "PRECIO $", 75), ("BS", "PRECIO BS", 95), ("STOCK", "STOCK", 60)]:
            self.tabla_cat.heading(col, text=tit)
            self.tabla_cat.column(col, width=anc, anchor="center")
        self.tabla_cat.column("NOM", anchor="w")
        self.tabla_cat.pack(fill="both", expand=True, padx=8, pady=8)
        self.tabla_cat.bind("<Double-1>", self.agregar_desde_tabla)

        f_car = ctk.CTkFrame(f_body)
        f_car.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=5)

        ctk.CTkLabel(f_car, text="🛒 CARRITO DE COMPRA ACTUAL", font=("Roboto", 13, "bold")).pack(pady=6)

        self.tabla_car = ttk.Treeview(f_car, columns=("CANT", "NOM", "UNIT", "SUB_USD", "SUB_BS"), show="headings", height=8)
        for col, tit, anc in [("CANT", "CANT", 55), ("NOM", "DESCRIPCIÓN", 170), ("UNIT", "P. UNIT $", 75), ("SUB_USD", "SUBT $", 80), ("SUB_BS", "SUBT BS", 100)]:
            self.tabla_car.heading(col, text=tit)
            self.tabla_car.column(col, width=anc, anchor="center")
        self.tabla_car.column("NOM", anchor="w")
        self.tabla_car.pack(fill="both", expand=True, padx=8, pady=4)

        f_car_acciones = ctk.CTkFrame(f_car, fg_color="transparent")
        f_car_acciones.pack(fill="x", padx=8, pady=4)
        ctk.CTkButton(f_car_acciones, text="➖ Quitar Seleccionado", fg_color="#e67e22", width=150, height=30, command=self.quitar_item).pack(side="left", padx=4)
        ctk.CTkButton(f_car_acciones, text="🗑️ Vaciar Carrito", fg_color="#e74c3c", width=130, height=30, command=self.vaciar_carrito).pack(side="right", padx=4)

        f_tot = ctk.CTkFrame(f_car, corner_radius=8)
        f_tot.pack(fill="x", padx=8, pady=6)

        self.lbl_total_usd = ctk.CTkLabel(f_tot, text="TOTAL $: $0.00", font=("Roboto", 22, "bold"), text_color="#3498db")
        self.lbl_total_usd.pack(pady=(8, 2))
        self.lbl_total_bs = ctk.CTkLabel(f_tot, text="TOTAL BS: Bs. 0.00", font=("Roboto", 24, "bold"), text_color="#2ecc71")
        self.lbl_total_bs.pack(pady=(0, 8))

        ctk.CTkLabel(f_car, text="⚡ COBRO DIRECTO EN 1 CLIC (Sin ventanas extra):", font=("Roboto", 12, "bold"), text_color="#f39c12").pack(pady=(2, 4))

        f_cobro_rapido = ctk.CTkFrame(f_car, fg_color="transparent")
        f_cobro_rapido.pack(fill="x", padx=8, pady=4)

        ctk.CTkButton(
            f_cobro_rapido, text="💵 EFECTIVO $\n(1 Clic)", fg_color="#27ae60", hover_color="#2ecc71",
            height=48, font=("Roboto", 13, "bold"), command=lambda: self.cobro_un_clic("EFECTIVO_USD")
        ).pack(side="left", fill="x", expand=True, padx=3)

        ctk.CTkButton(
            f_cobro_rapido, text="💳 PUNTO BS\n(1 Clic)", fg_color="#2980b9", hover_color="#3498db",
            height=48, font=("Roboto", 13, "bold"), command=lambda: self.cobro_un_clic("PUNTO_BS")
        ).pack(side="left", fill="x", expand=True, padx=3)

        ctk.CTkButton(
            f_cobro_rapido, text="📱 PAGO MÓVIL\n(1 Clic)", fg_color="#8e44ad", hover_color="#9b59b6",
            height=48, font=("Roboto", 13, "bold"), command=lambda: self.cobro_un_clic("PM_BS")
        ).pack(side="left", fill="x", expand=True, padx=3)

        ctk.CTkButton(
            f_car, text="🧮 PAGO MIXTO / CALCULAR VUELTO / REFERENCIA",
            fg_color="#34495e", hover_color="#2c3e50", height=38, font=("Roboto", 13, "bold"),
            command=self.abrir_modal_pago_mixto
        ).pack(fill="x", padx=10, pady=(4, 10))

        self.refrescar()

    def mostrar_toast(self, texto, color="#2ecc71"):
        self.lbl_toast.configure(text=texto, text_color=color)
        self.after(4500, lambda: self.lbl_toast.configure(text=""))

    def toggle_mayor(self):
        self.modo_mayor = (self.sw_mayor.get() == 1)
        self.refrescar()

    def obtener_cantidad_input(self):
        try:
            val = float(self.ent_cant.get().replace(',', '.'))
            return val if val > 0 else 1.0
        except Exception:
            return 1.0

    def refrescar(self, filtro=""):
        for i in self.tabla_cat.get_children():
            self.tabla_cat.delete(i)
        conn = database.conectar_db()
        c = conn.cursor()
        if filtro:
            c.execute("""SELECT id, codigo_barras, nombre, precio_venta_usd, precio_mayor_usd, stock_actual, costo_usd 
                         FROM Productos WHERE codigo_barras LIKE ? OR nombre LIKE ?""", (f"%{filtro}%", f"%{filtro}%"))
        else:
            c.execute("SELECT id, codigo_barras, nombre, precio_venta_usd, precio_mayor_usd, stock_actual, costo_usd FROM Productos")

        tasa = self.app_parent.tasa_actual
        for p in c.fetchall():
            precio = p[4] if (self.modo_mayor and p[4] and p[4] > 0) else p[3]
            bs = precio * tasa
            self.tabla_cat.insert("", "end", values=(p[0], p[1], p[2], f"${precio:.2f}", f"Bs. {bs:.2f}", p[5]))
        conn.close()
        self.actualizar_vista_carrito()

    def filtrar_catalogo(self, event=None):
        self.refrescar(self.ent_buscar.get().strip())

    def agregar_primer_resultado(self, event=None):
        items = self.tabla_cat.get_children()
        if items:
            prod_id = self.tabla_cat.item(items[0])['values'][0]
            self.agregar_producto_por_id(prod_id)
            self.ent_buscar.delete(0, 'end')
            self.refrescar()

    def agregar_desde_tabla(self, event=None):
        sel = self.tabla_cat.selection()
        if sel:
            prod_id = self.tabla_cat.item(sel[0])['values'][0]
            self.agregar_producto_por_id(prod_id)

    def agregar_producto_por_id(self, prod_id):
        cant = self.obtener_cantidad_input()
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("SELECT id, nombre, precio_venta_usd, precio_mayor_usd, stock_actual, costo_usd FROM Productos WHERE id=?", (prod_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return

        precio = row[3] if (self.modo_mayor and row[3] and row[3] > 0) else row[2]
        if precio <= 0:
            messagebox.showwarning("Precio en $0.00", f"El producto '{row[1]}' tiene precio $0.00. Edítelo en Inventario antes de venderlo.")
            return

        for item in self.carrito:
            if item['id'] == row[0]:
                item['cantidad'] += cant
                item['precio_usd'] = precio
                item['subtotal_usd'] = round(item['cantidad'] * precio, 2)
                self.ent_cant.delete(0, 'end')
                self.ent_cant.insert(0, "1")
                self.actualizar_vista_carrito()
                return

        self.carrito.append({
            'id': row[0],
            'nombre': row[1],
            'cantidad': cant,
            'precio_usd': precio,
            'costo_usd': row[5] or 0.0,
            'subtotal_usd': round(cant * precio, 2)
        })
        self.ent_cant.delete(0, 'end')
        self.ent_cant.insert(0, "1")
        self.actualizar_vista_carrito()

    def actualizar_vista_carrito(self):
        for i in self.tabla_car.get_children():
            self.tabla_car.delete(i)
        tasa = self.app_parent.tasa_actual
        total_usd = 0.0
        for item in self.carrito:
            sub_usd = item['subtotal_usd']
            sub_bs = sub_usd * tasa
            total_usd += sub_usd
            self.tabla_car.insert("", "end", values=(
                item['cantidad'], item['nombre'], f"${item['precio_usd']:.2f}", f"${sub_usd:.2f}", f"Bs. {sub_bs:.2f}"
            ))
        total_bs = total_usd * tasa
        self.lbl_total_usd.configure(text=f"TOTAL $: ${total_usd:.2f}")
        self.lbl_total_bs.configure(text=f"TOTAL BS: Bs. {total_bs:.2f}")

    def quitar_item(self):
        sel = self.tabla_car.selection()
        if sel:
            idx = self.tabla_car.index(sel[0])
            if 0 <= idx < len(self.carrito):
                self.carrito.pop(idx)
                self.actualizar_vista_carrito()

    def vaciar_carrito(self):
        self.carrito.clear()
        self.actualizar_vista_carrito()

    def cobro_un_clic(self, tipo):
        if not self.carrito:
            self.mostrar_toast("⚠️ Agregue productos al carrito primero", "#e67e22")
            return

        tasa = self.app_parent.tasa_actual
        total_usd = round(sum(i['subtotal_usd'] for i in self.carrito), 2)
        total_bs = round(total_usd * tasa, 2)

        if tipo == "EFECTIVO_USD":
            metodo_str = f"Efec $: {total_usd:.1f}"
        elif tipo == "PUNTO_BS":
            metodo_str = f"Punto Bs: {total_bs:.2f}"
        else:
            metodo_str = f"PM Bs: {total_bs:.2f} (Ref:Rapido)"

        try:
            venta_id, _ = VentasController.procesar_venta(self.carrito, total_usd, total_bs, tasa, metodo_str)
            self.vaciar_carrito()
            self.refrescar()
            self.mostrar_toast(f"✅ Venta #{venta_id:06d} cobrada en 1 clic ({metodo_str})")
            self.ent_buscar.focus()
        except Exception as e:
            messagebox.showerror("Error al procesar venta", str(e))

    def abrir_modal_pago_mixto(self):
        if not self.carrito:
            self.mostrar_toast("⚠️ El carrito está vacío", "#e67e22")
            return

        tasa = self.app_parent.tasa_actual
        total_usd = round(sum(i['subtotal_usd'] for i in self.carrito), 2)
        total_bs = round(total_usd * tasa, 2)

        modal = ctk.CTkToplevel(self)
        modal.title("Calculadora de Pago Mixto y Vuelto")
        modal.geometry("460x520")
        modal.grab_set()
        modal.focus()

        ctk.CTkLabel(modal, text=f"TOTAL A COBRAR: ${total_usd:.2f}", font=("Roboto", 20, "bold"), text_color="#3498db").pack(pady=(15, 2))
        ctk.CTkLabel(modal, text=f"Equivalente: Bs. {total_bs:.2f}", font=("Roboto", 18, "bold"), text_color="#2ecc71").pack(pady=(0, 15))

        f_campos = ctk.CTkFrame(modal, fg_color="transparent")
        f_campos.pack(fill="x", padx=25)

        ctk.CTkLabel(f_campos, text="Efectivo Recibido ($):").grid(row=0, column=0, pady=6, sticky="e", padx=5)
        e_efec_usd = ctk.CTkEntry(f_campos, width=160, validate="key", validatecommand=self.vcmd_num)
        e_efec_usd.insert(0, f"{total_usd:.2f}")
        e_efec_usd.grid(row=0, column=1, pady=6, padx=5)

        ctk.CTkLabel(f_campos, text="Punto de Venta (Bs):").grid(row=1, column=0, pady=6, sticky="e", padx=5)
        e_punto_bs = ctk.CTkEntry(f_campos, width=160, validate="key", validatecommand=self.vcmd_num)
        e_punto_bs.insert(0, "0")
        e_punto_bs.grid(row=1, column=1, pady=6, padx=5)

        ctk.CTkLabel(f_campos, text="Pago Móvil / Efec (Bs):").grid(row=2, column=0, pady=6, sticky="e", padx=5)
        e_pm_bs = ctk.CTkEntry(f_campos, width=160, validate="key", validatecommand=self.vcmd_num)
        e_pm_bs.insert(0, "0")
        e_pm_bs.grid(row=2, column=1, pady=6, padx=5)

        ctk.CTkLabel(f_campos, text="Nro. Referencia (Opcional):").grid(row=3, column=0, pady=6, sticky="e", padx=5)
        e_ref = ctk.CTkEntry(f_campos, width=160)
        e_ref.grid(row=3, column=1, pady=6, padx=5)

        lbl_estado_pago = ctk.CTkLabel(modal, text="✅ Pago Exacto Cubierto", font=("Roboto", 15, "bold"), text_color="#2ecc71")
        lbl_estado_pago.pack(pady=15)

        def leer_float(entry):
            try:
                return float(entry.get().replace(',', '.'))
            except Exception:
                return 0.0

        def recalcular(event=None):
            abonado_usd = leer_float(e_efec_usd) + ((leer_float(e_punto_bs) + leer_float(e_pm_bs)) / tasa)
            diferencia = abonado_usd - total_usd
            if diferencia < -0.01:
                faltante_usd = abs(diferencia)
                lbl_estado_pago.configure(
                    text=f"⚠️ Restan por cubrir: ${faltante_usd:.2f} (Bs. {faltante_usd * tasa:.2f})",
                    text_color="#e67e22"
                )
            elif diferencia > 0.01:
                lbl_estado_pago.configure(
                    text=f"💵 VUELTO AL CLIENTE: ${diferencia:.2f} (Bs. {diferencia * tasa:.2f})",
                    text_color="#2ecc71"
                )
            else:
                lbl_estado_pago.configure(text="✅ Pago Exacto Cubierto", text_color="#2ecc71")

        for ent in [e_efec_usd, e_punto_bs, e_pm_bs]:
            ent.bind("<KeyRelease>", recalcular)

        def confirmar_cobro_mixto():
            v_efec = leer_float(e_efec_usd)
            v_punto = leer_float(e_punto_bs)
            v_pm = leer_float(e_pm_bs)
            abonado_usd = v_efec + ((v_punto + v_pm) / tasa)

            if abonado_usd < (total_usd - 0.02):
                messagebox.showwarning("Monto Insuficiente", "El monto ingresado aún no cubre el total de la venta.", parent=modal)
                return

            partes = []
            if v_efec > 0:
                partes.append(f"Efec $: {v_efec:.2f}")
            if v_punto > 0:
                partes.append(f"Punto Bs: {v_punto:.2f}")
            if v_pm > 0:
                partes.append(f"PM Bs: {v_pm:.2f} (Ref:{e_ref.get().strip()})")
            metodo_final = " + ".join(partes) if partes else f"Efec $: {total_usd:.2f}"

            try:
                venta_id, _ = VentasController.procesar_venta(self.carrito, total_usd, total_bs, tasa, metodo_final)
                modal.destroy()
                self.vaciar_carrito()
                self.refrescar()
                self.mostrar_toast(f"✅ Venta #{venta_id:06d} registrada con éxito")
                self.ent_buscar.focus()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=modal)

        ctk.CTkButton(
            modal, text="✅ CONFIRMAR Y GENERAR TICKET", fg_color="#2ecc71", hover_color="#27ae60",
            height=45, font=("Roboto", 14, "bold"), command=confirmar_cobro_mixto
        ).pack(fill="x", padx=35, pady=10)