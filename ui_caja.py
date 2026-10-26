import customtkinter as ctk
from tkinter import ttk, messagebox
import re
import database
from controlador_ventas import VentasController
from controlador_configuracion import ConfigController

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
        f_top.pack(fill="x", padx=15, pady=(8, 5))

        self.ent_buscar = ctk.CTkEntry(
            f_top,
            placeholder_text="🔍 Escanee código de barras o busque producto (Enter para añadir)...",
            width=450,
            height=42,
            font=("Roboto", 14, "bold")
        )
        self.ent_buscar.pack(side="left", padx=(0, 10))
        self.ent_buscar.bind("<KeyRelease>", self.filtrar_catalogo)
        self.ent_buscar.bind("<Return>", self.agregar_primer_resultado)

        ctk.CTkLabel(f_top, text="Cant / Peso:", font=("Roboto", 14, "bold")).pack(side="left", padx=4)
        self.ent_cant = ctk.CTkEntry(f_top, width=80, height=42, font=("Roboto", 15, "bold"), validate="key", validatecommand=self.vcmd_num)
        self.ent_cant.insert(0, "1")
        self.ent_cant.pack(side="left", padx=4)

        self.sw_mayor = ctk.CTkSwitch(f_top, text="Precio Mayor", command=self.toggle_mayor, font=("Roboto", 13, "bold"))
        self.sw_mayor.pack(side="left", padx=12)

        self.lbl_toast = ctk.CTkLabel(f_top, text="", font=("Roboto", 14, "bold"), text_color="#2ecc71")
        self.lbl_toast.pack(side="right", padx=10)

        f_body = ctk.CTkFrame(self, fg_color="transparent")
        f_body.pack(fill="both", expand=True, padx=15, pady=5)
        f_body.grid_columnconfigure(0, weight=5)
        f_body.grid_columnconfigure(1, weight=5)
        f_body.grid_rowconfigure(0, weight=1)

        # IZQUIERDA: Catálogo
        f_cat = ctk.CTkFrame(f_body)
        f_cat.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=5)

        ctk.CTkLabel(f_cat, text="📦 CATÁLOGO DE PRODUCTOS (Doble clic para añadir)", font=("Roboto", 14, "bold")).pack(pady=8)

        self.tabla_cat = ttk.Treeview(f_cat, columns=("ID", "COD", "NOM", "UM", "USD", "BS", "STOCK"), show="headings")
        for col, tit, anc in [
            ("ID", "ID", 35), ("COD", "CÓD", 65), ("NOM", "PRODUCTO", 165),
            ("UM", "U.M", 55), ("USD", "PRECIO $", 75), ("BS", "PRECIO BS", 95), ("STOCK", "STOCK", 65)
        ]:
            self.tabla_cat.heading(col, text=tit)
            self.tabla_cat.column(col, width=anc, anchor="center")
        self.tabla_cat.column("NOM", anchor="w")
        self.tabla_cat.pack(fill="both", expand=True, padx=8, pady=5)
        self.tabla_cat.bind("<Double-1>", self.agregar_desde_tabla)

        f_cat_btns = ctk.CTkFrame(f_cat, fg_color="transparent")
        f_cat_btns.pack(fill="x", padx=8, pady=6)
        ctk.CTkButton(
            f_cat_btns, text="⚖️ VENDER POR GRAMOS / BALANZA / MONTO",
            fg_color="#d35400", hover_color="#e67e22", height=38, font=("Roboto", 13, "bold"),
            command=self.abrir_asistente_granel_seleccionado
        ).pack(fill="x", padx=4)

        # DERECHA: Carrito y Controles de Cantidad
        f_car = ctk.CTkFrame(f_body)
        f_car.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=5)

        ctk.CTkLabel(f_car, text="🛒 CARRITO DE COMPRA ACTUAL", font=("Roboto", 14, "bold")).pack(pady=8)

        self.tabla_car = ttk.Treeview(f_car, columns=("CANT", "NOM", "UNIT", "SUB_USD", "SUB_BS"), show="headings", height=7)
        for col, tit, anc in [
            ("CANT", "CANT/PESO", 80), ("NOM", "DESCRIPCIÓN", 160),
            ("UNIT", "P. BASE $", 75), ("SUB_USD", "SUBT $", 80), ("SUB_BS", "SUBT BS", 100)
        ]:
            self.tabla_car.heading(col, text=tit)
            self.tabla_car.column(col, width=anc, anchor="center")
        self.tabla_car.column("NOM", anchor="w")
        self.tabla_car.pack(fill="both", expand=True, padx=8, pady=4)
        self.tabla_car.bind("<Double-1>", lambda e: self.editar_item_carrito())

        # Botonera de Edición de Carrito (Subir, Bajar, Cambiar Gramos/Cant, Quitar)
        f_car_acciones = ctk.CTkFrame(f_car, fg_color="transparent")
        f_car_acciones.pack(fill="x", padx=8, pady=4)

        ctk.CTkButton(f_car_acciones, text="➕", width=42, height=34, font=("Roboto", 15, "bold"), fg_color="#27ae60", command=lambda: self.ajustar_cant_carrito(1)).pack(side="left", padx=2)
        ctk.CTkButton(f_car_acciones, text="➖", width=42, height=34, font=("Roboto", 15, "bold"), fg_color="#f39c12", command=lambda: self.ajustar_cant_carrito(-1)).pack(side="left", padx=2)
        ctk.CTkButton(f_car_acciones, text="✏️ Cant / Gramos", width=135, height=34, font=("Roboto", 12, "bold"), fg_color="#2980b9", command=self.editar_item_carrito).pack(side="left", padx=4)
        ctk.CTkButton(f_car_acciones, text="🗑️ Quitar", width=85, height=34, font=("Roboto", 12, "bold"), fg_color="#e67e22", command=self.quitar_item).pack(side="left", padx=2)
        ctk.CTkButton(f_car_acciones, text="Vaciar", width=75, height=34, font=("Roboto", 12, "bold"), fg_color="#c0392b", command=self.vaciar_carrito).pack(side="right", padx=2)

        # Panel de Totales Grandes
        f_tot = ctk.CTkFrame(f_car, corner_radius=8)
        f_tot.pack(fill="x", padx=8, pady=6)

        self.lbl_total_usd = ctk.CTkLabel(f_tot, text="TOTAL $: $0.00", font=("Roboto", 24, "bold"), text_color="#3498db")
        self.lbl_total_usd.pack(pady=(6, 2))
        self.lbl_total_bs = ctk.CTkLabel(f_tot, text="TOTAL BS: Bs. 0.00", font=("Roboto", 26, "bold"), text_color="#2ecc71")
        self.lbl_total_bs.pack(pady=(0, 6))

        ctk.CTkLabel(f_car, text="⚡ COBRO DIRECTO EN 1 CLIC:", font=("Roboto", 13, "bold"), text_color="#f39c12").pack(pady=(2, 4))

        f_cobro_rapido = ctk.CTkFrame(f_car, fg_color="transparent")
        f_cobro_rapido.pack(fill="x", padx=8, pady=4)

        ctk.CTkButton(
            f_cobro_rapido, text="💵 EFECTIVO $\n(1 Clic)", fg_color="#27ae60", hover_color="#2ecc71",
            height=50, font=("Roboto", 14, "bold"), command=lambda: self.cobro_un_clic("EFECTIVO_USD")
        ).pack(side="left", fill="x", expand=True, padx=3)

        ctk.CTkButton(
            f_cobro_rapido, text="💳 PUNTO BS\n(1 Clic)", fg_color="#2980b9", hover_color="#3498db",
            height=50, font=("Roboto", 14, "bold"), command=lambda: self.cobro_un_clic("PUNTO_BS")
        ).pack(side="left", fill="x", expand=True, padx=3)

        ctk.CTkButton(
            f_cobro_rapido, text="📱 PAGO MÓVIL\n(1 Clic)", fg_color="#8e44ad", hover_color="#9b59b6",
            height=50, font=("Roboto", 14, "bold"), command=lambda: self.cobro_un_clic("PM_BS")
        ).pack(side="left", fill="x", expand=True, padx=3)

        ctk.CTkButton(
            f_car, text="🧮 PAGO MIXTO / CALCULAR VUELTO / REFERENCIA",
            fg_color="#34495e", hover_color="#2c3e50", height=40, font=("Roboto", 14, "bold"),
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
            c.execute("""SELECT id, codigo_barras, nombre, unidad_medida, precio_venta_usd, precio_mayor_usd, stock_actual 
                         FROM Productos WHERE codigo_barras LIKE ? OR nombre LIKE ?""", (f"%{filtro}%", f"%{filtro}%"))
        else:
            c.execute("SELECT id, codigo_barras, nombre, unidad_medida, precio_venta_usd, precio_mayor_usd, stock_actual FROM Productos")

        tasa = self.app_parent.tasa_actual
        for p in c.fetchall():
            um = p[3] or "Unidad"
            precio = p[5] if (self.modo_mayor and p[5] and p[5] > 0) else p[4]
            bs = precio * tasa
            stock_fmt = f"{p[6]:.3f}" if um in ["KG", "LITRO"] else f"{p[6]:g}"
            self.tabla_cat.insert("", "end", values=(p[0], p[1], p[2], um, f"${precio:.2f}", f"Bs. {bs:.2f}", stock_fmt))
        conn.close()
        self.actualizar_vista_carrito()

    def filtrar_catalogo(self, event=None):
        self.refrescar(self.ent_buscar.get().strip())

    def agregar_primer_resultado(self, event=None):
        items = self.tabla_cat.get_children()
        if items:
            prod_id = self.tabla_cat.item(items[0])['values'][0]
            self.procesar_seleccion_producto(prod_id)
            self.ent_buscar.delete(0, 'end')
            self.refrescar()

    def agregar_desde_tabla(self, event=None):
        sel = self.tabla_cat.selection()
        if sel:
            prod_id = self.tabla_cat.item(sel[0])['values'][0]
            self.procesar_seleccion_producto(prod_id)

    def abrir_asistente_granel_seleccionado(self):
        sel = self.tabla_cat.selection()
        if not sel:
            messagebox.showinfo("Seleccione un Producto", "Seleccione primero un producto del catálogo para pesarlo o fraccionarlo.")
            return
        prod_id = self.tabla_cat.item(sel[0])['values'][0]
        self.abrir_modal_balanza_granel(prod_id)

    def procesar_seleccion_producto(self, prod_id):
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("SELECT id, nombre, unidad_medida, precio_venta_usd, precio_mayor_usd, stock_actual, costo_usd FROM Productos WHERE id=?", (prod_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return

        um = (row[2] or "Unidad").upper()
        # Si el producto es por KG, GR o LITRO y la casilla Cant sigue en "1", abrimos el asistente de Gramos/Balanza
        if um in ["KG", "GR", "LITRO"] and self.ent_cant.get().strip() == "1":
            self.abrir_modal_balanza_granel(prod_id)
        else:
            cant = self.obtener_cantidad_input()
            self.insertar_en_carrito(row, cant)

    def insertar_en_carrito(self, row, cantidad, reemplazar=False):
        prod_id, nombre, um, p_detal, p_mayor, stock, costo = row
        um = (um or "Unidad").upper()
        precio = p_mayor if (self.modo_mayor and p_mayor and p_mayor > 0) else p_detal

        if precio <= 0:
            messagebox.showwarning("Precio en $0.00", f"El producto '{nombre}' tiene precio $0.00. Edítelo en Inventario.")
            return

        for item in self.carrito:
            if item['id'] == prod_id:
                item['cantidad'] = round(cantidad if reemplazar else (item['cantidad'] + cantidad), 4)
                item['precio_usd'] = precio
                item['subtotal_usd'] = round(item['cantidad'] * precio, 2)
                self.ent_cant.delete(0, 'end')
                self.ent_cant.insert(0, "1")
                self.actualizar_vista_carrito()
                return

        self.carrito.append({
            'id': prod_id,
            'nombre': nombre,
            'um': um,
            'cantidad': round(cantidad, 4),
            'precio_usd': precio,
            'costo_usd': costo or 0.0,
            'subtotal_usd': round(cantidad * precio, 2)
        })
        self.ent_cant.delete(0, 'end')
        self.ent_cant.insert(0, "1")
        self.actualizar_vista_carrito()

    def abrir_modal_balanza_granel(self, prod_id, item_carrito_existente=None):
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("SELECT id, nombre, unidad_medida, precio_venta_usd, precio_mayor_usd, stock_actual, costo_usd FROM Productos WHERE id=?", (prod_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return

        _, nombre, um, p_detal, p_mayor, _, _ = row
        um = (um or "KG").upper()
        precio_base = p_mayor if (self.modo_mayor and p_mayor and p_mayor > 0) else p_detal
        tasa = self.app_parent.tasa_actual

        # Determinar precio por KG para conversiones exactas
        precio_por_kg = precio_base * 1000.0 if um == "GR" else precio_base

        modal = ctk.CTkToplevel(self)
        modal.title(f"⚖️ Venta a Granel y Balanza — {nombre}")
        modal.geometry("480x500")
        modal.grab_set()
        modal.focus()

        ctk.CTkLabel(modal, text=f"📦 {nombre}", font=("Roboto", 20, "bold"), text_color="#3498db").pack(pady=(15, 2))
        ctk.CTkLabel(
            modal,
            text=f"Precio Base: ${precio_base:.2f} por {um}  (Bs. {precio_base * tasa:.2f})",
            font=("Roboto", 14, "bold"), text_color="#2ecc71"
        ).pack(pady=(0, 12))

        # Botón para leer desde Balanza Electrónica por Puerto Serial COM
        ctk.CTkButton(
            modal, text="📡 LEER PESO DE BALANZA ELECTRÓNICA (COM)",
            fg_color="#8e44ad", hover_color="#9b59b6", height=38, font=("Roboto", 13, "bold"),
            command=lambda: leer_balanza_serial()
        ).pack(fill="x", padx=30, pady=6)

        f_form = ctk.CTkFrame(modal)
        f_form.pack(fill="x", padx=25, pady=10)

        ctk.CTkLabel(f_form, text="Peso en GRAMOS (ej. 250):", font=("Roboto", 13, "bold")).grid(row=0, column=0, padx=10, pady=8, sticky="e")
        e_gramos = ctk.CTkEntry(f_form, width=150, font=("Roboto", 15, "bold"), validate="key", validatecommand=self.vcmd_num)
        e_gramos.grid(row=0, column=1, padx=10, pady=8)

        ctk.CTkLabel(f_form, text="Peso en KILOS / LITROS (ej. 0.250):", font=("Roboto", 13, "bold")).grid(row=1, column=0, padx=10, pady=8, sticky="e")
        e_kilos = ctk.CTkEntry(f_form, width=150, font=("Roboto", 15, "bold"), validate="key", validatecommand=self.vcmd_num)
        e_kilos.grid(row=1, column=1, padx=10, pady=8)

        ctk.CTkLabel(f_form, text="O cobrar por MONTO $:", font=("Roboto", 13, "bold"), text_color="#3498db").grid(row=2, column=0, padx=10, pady=8, sticky="e")
        e_monto_usd = ctk.CTkEntry(f_form, width=150, font=("Roboto", 15, "bold"), validate="key", validatecommand=self.vcmd_num)
        e_monto_usd.grid(row=2, column=1, padx=10, pady=8)

        ctk.CTkLabel(f_form, text="O cobrar por MONTO Bs:", font=("Roboto", 13, "bold"), text_color="#2ecc71").grid(row=3, column=0, padx=10, pady=8, sticky="e")
        e_monto_bs = ctk.CTkEntry(f_form, width=150, font=("Roboto", 15, "bold"), validate="key", validatecommand=self.vcmd_num)
        e_monto_bs.grid(row=3, column=1, padx=10, pady=8)

        lbl_resumen = ctk.CTkLabel(modal, text="Ingrese los gramos, kilos o el monto a despachar", font=("Roboto", 15, "bold"), text_color="#f39c12")
        lbl_resumen.pack(pady=10)

        def _set_val(entry, val_str):
            entry.delete(0, 'end')
            entry.insert(0, val_str)

        def desde_gramos(event=None):
            try:
                g = float(e_gramos.get().replace(',', '.'))
                kg = g / 1000.0
                usd = (g * precio_base) if um == "GR" else (kg * precio_por_kg)
                bs = usd * tasa
                _set_val(e_kilos, f"{kg:.3f}")
                _set_val(e_monto_usd, f"{usd:.2f}")
                _set_val(e_monto_bs, f"{bs:.2f}")
                lbl_resumen.configure(text=f"✅ Despachar: {g:.0f} g ({kg:.3f} kg)  ➔  ${usd:.2f} / Bs. {bs:.2f}", text_color="#2ecc71")
            except Exception:
                pass

        def desde_kilos(event=None):
            try:
                kg = float(e_kilos.get().replace(',', '.'))
                g = kg * 1000.0
                usd = (g * precio_base) if um == "GR" else (kg * precio_por_kg)
                bs = usd * tasa
                _set_val(e_gramos, f"{g:.0f}")
                _set_val(e_monto_usd, f"{usd:.2f}")
                _set_val(e_monto_bs, f"{bs:.2f}")
                lbl_resumen.configure(text=f"✅ Despachar: {g:.0f} g ({kg:.3f} kg)  ➔  ${usd:.2f} / Bs. {bs:.2f}", text_color="#2ecc71")
            except Exception:
                pass

        def desde_usd(event=None):
            try:
                usd = float(e_monto_usd.get().replace(',', '.'))
                kg = usd / precio_por_kg if precio_por_kg > 0 else 0
                g = kg * 1000.0
                bs = usd * tasa
                _set_val(e_gramos, f"{g:.0f}")
                _set_val(e_kilos, f"{kg:.3f}")
                _set_val(e_monto_bs, f"{bs:.2f}")
                lbl_resumen.configure(text=f"✅ Despachar: {g:.0f} g ({kg:.3f} kg)  ➔  ${usd:.2f} / Bs. {bs:.2f}", text_color="#2ecc71")
            except Exception:
                pass

        def desde_bs(event=None):
            try:
                bs = float(e_monto_bs.get().replace(',', '.'))
                usd = bs / tasa if tasa > 0 else 0
                kg = usd / precio_por_kg if precio_por_kg > 0 else 0
                g = kg * 1000.0
                _set_val(e_gramos, f"{g:.0f}")
                _set_val(e_kilos, f"{kg:.3f}")
                _set_val(e_monto_usd, f"{usd:.2f}")
                lbl_resumen.configure(text=f"✅ Despachar: {g:.0f} g ({kg:.3f} kg)  ➔  ${usd:.2f} / Bs. {bs:.2f}", text_color="#2ecc71")
            except Exception:
                pass

        e_gramos.bind("<KeyRelease>", desde_gramos)
        e_kilos.bind("<KeyRelease>", desde_kilos)
        e_monto_usd.bind("<KeyRelease>", desde_usd)
        e_monto_bs.bind("<KeyRelease>", desde_bs)

        def leer_balanza_serial():
            conf = ConfigController.obtener_config()
            puerto = conf[8] if len(conf) > 8 else "COM3"
            try:
                import serial
                with serial.Serial(puerto, baudrate=9600, timeout=1.5) as ser:
                    ser.write(b'P\r\n')
                    linea = ser.readline().decode('ascii', errors='ignore').strip()
                    match = re.search(r'(\d+\.\d+|\d+)', linea)
                    if match:
                        valor = float(match.group(1))
                        # Si la balanza envía en KG (ej. 0.450) o en GR (ej. 450)
                        if "." in match.group(1) or valor < 30:
                            _set_val(e_kilos, f"{valor:.3f}")
                            desde_kilos()
                        else:
                            _set_val(e_gramos, f"{valor:.0f}")
                            desde_gramos()
                    else:
                        messagebox.showwarning("Balanza", f"No se detectó lectura estable en {puerto}.", parent=modal)
            except ImportError:
                messagebox.showinfo("Módulo Serial", "Para conectar balanza física ejecute: pip install pyserial\nPuede ingresar los gramos manualmente abajo.", parent=modal)
            except Exception as e:
                messagebox.showwarning("Balanza no detectada", f"No se pudo abrir el puerto {puerto}.\nVerifique el puerto en Configuración o ingrese los gramos manualmente.\nDetalle: {e}", parent=modal)

        def confirmar_peso():
            try:
                g = float(e_gramos.get().replace(',', '.'))
                kg = float(e_kilos.get().replace(',', '.'))
            except Exception:
                messagebox.showwarning("Peso inválido", "Ingrese una cantidad válida en gramos o kilos.", parent=modal)
                return

            cantidad_final = g if um == "GR" else (kg if um in ["KG", "LITRO"] else kg)
            if cantidad_final <= 0:
                messagebox.showwarning("Peso en cero", "El peso debe ser mayor a cero.", parent=modal)
                return

            self.insertar_en_carrito(row, cantidad_final, reemplazar=(item_carrito_existente is not None))
            modal.destroy()

        # Pre-cargar valores si se está editando desde el carrito
        if item_carrito_existente:
            cant_actual = item_carrito_existente['cantidad']
            if um == "GR":
                _set_val(e_gramos, f"{cant_actual:.0f}")
                desde_gramos()
            else:
                _set_val(e_kilos, f"{cant_actual:.3f}")
                desde_kilos()
        else:
            e_gramos.focus()

        ctk.CTkButton(
            modal, text="✅ AGREGAR AL CARRITO", fg_color="#27ae60", hover_color="#2ecc71",
            height=44, font=("Roboto", 15, "bold"), command=confirmar_peso
        ).pack(fill="x", padx=30, pady=10)

    def ajustar_cant_carrito(self, delta):
        sel = self.tabla_car.selection()
        if not sel:
            self.mostrar_toast("Seleccione un producto del carrito para ajustar su cantidad", "#f39c12")
            return
        idx = self.tabla_car.index(sel[0])
        if 0 <= idx < len(self.carrito):
            item = self.carrito[idx]
            paso = 0.1 if item.get('um') in ['KG', 'LITRO'] else (50 if item.get('um') == 'GR' else 1)
            nueva = round(item['cantidad'] + (delta * paso), 4)
            if nueva <= 0:
                self.carrito.pop(idx)
            else:
                item['cantidad'] = nueva
                item['subtotal_usd'] = round(nueva * item['precio_usd'], 2)
            self.actualizar_vista_carrito()

    def editar_item_carrito(self):
        sel = self.tabla_car.selection()
        if not sel:
            self.mostrar_toast("Seleccione una fila del carrito para cambiar su cantidad o gramos", "#f39c12")
            return
        idx = self.tabla_car.index(sel[0])
        if 0 <= idx < len(self.carrito):
            item = self.carrito[idx]
            if item.get('um') in ['KG', 'GR', 'LITRO']:
                self.abrir_modal_balanza_granel(item['id'], item_carrito_existente=item)
            else:
                dialogo = ctk.CTkInputDialog(text=f"Nueva cantidad para {item['nombre']}:", title="Modificar Cantidad")
                val = dialogo.get_input()
                if val:
                    try:
                        nueva_c = float(val.replace(',', '.'))
                        if nueva_c > 0:
                            item['cantidad'] = nueva_c
                            item['subtotal_usd'] = round(nueva_c * item['precio_usd'], 2)
                            self.actualizar_vista_carrito()
                    except Exception:
                        messagebox.showwarning("Valor Inválido", "Ingrese solo números.")

    def actualizar_vista_carrito(self):
        for i in self.tabla_car.get_children():
            self.tabla_car.delete(i)
        tasa = self.app_parent.tasa_actual
        total_usd = 0.0
        for item in self.carrito:
            sub_usd = item['subtotal_usd']
            sub_bs = sub_usd * tasa
            total_usd += sub_usd
            um = item.get('um', 'Unidad')
            c_val = item['cantidad']
            if um == "KG" and c_val < 1.0:
                cant_mostrar = f"{c_val * 1000:.0f} g ({c_val:.3f}kg)"
            elif um in ["KG", "LITRO"]:
                cant_mostrar = f"{c_val:.3f} {um}"
            elif um == "GR":
                cant_mostrar = f"{c_val:.0f} g"
            else:
                cant_mostrar = f"{c_val:g} und"

            self.tabla_car.insert("", "end", values=(
                cant_mostrar, item['nombre'], f"${item['precio_usd']:.2f}", f"${sub_usd:.2f}", f"Bs. {sub_bs:.2f}"
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
            metodo_str = f"Efec $: {total_usd:.2f}"
        elif tipo == "PUNTO_BS":
            metodo_str = f"Punto Bs: {total_bs:.2f}"
        else:
            metodo_str = f"PM Bs: {total_bs:.2f} (Ref:Directo)"

        try:
            venta_id, _ = VentasController.procesar_venta(self.carrito, total_usd, total_bs, tasa, metodo_str)
            self.vaciar_carrito()
            self.refrescar()
            self.mostrar_toast(f"✅ Venta #{venta_id:06d} registrada ({metodo_str})")
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

        ctk.CTkLabel(modal, text=f"TOTAL A COBRAR: ${total_usd:.2f}", font=("Roboto", 22, "bold"), text_color="#3498db").pack(pady=(15, 2))
        ctk.CTkLabel(modal, text=f"Equivalente: Bs. {total_bs:.2f}", font=("Roboto", 19, "bold"), text_color="#2ecc71").pack(pady=(0, 15))

        f_campos = ctk.CTkFrame(modal, fg_color="transparent")
        f_campos.pack(fill="x", padx=25)

        ctk.CTkLabel(f_campos, text="Efectivo Recibido ($):", font=("Roboto", 13, "bold")).grid(row=0, column=0, pady=6, sticky="e", padx=5)
        e_efec_usd = ctk.CTkEntry(f_campos, width=160, font=("Roboto", 14, "bold"), validate="key", validatecommand=self.vcmd_num)
        e_efec_usd.insert(0, f"{total_usd:.2f}")
        e_efec_usd.grid(row=0, column=1, pady=6, padx=5)

        ctk.CTkLabel(f_campos, text="Punto de Venta (Bs):", font=("Roboto", 13, "bold")).grid(row=1, column=0, pady=6, sticky="e", padx=5)
        e_punto_bs = ctk.CTkEntry(f_campos, width=160, font=("Roboto", 14, "bold"), validate="key", validatecommand=self.vcmd_num)
        e_punto_bs.insert(0, "0")
        e_punto_bs.grid(row=1, column=1, pady=6, padx=5)

        ctk.CTkLabel(f_campos, text="Pago Móvil / Efec (Bs):", font=("Roboto", 13, "bold")).grid(row=2, column=0, pady=6, sticky="e", padx=5)
        e_pm_bs = ctk.CTkEntry(f_campos, width=160, font=("Roboto", 14, "bold"), validate="key", validatecommand=self.vcmd_num)
        e_pm_bs.insert(0, "0")
        e_pm_bs.grid(row=2, column=1, pady=6, padx=5)

        ctk.CTkLabel(f_campos, text="Nro. Referencia:", font=("Roboto", 13, "bold")).grid(row=3, column=0, pady=6, sticky="e", padx=5)
        e_ref = ctk.CTkEntry(f_campos, width=160, font=("Roboto", 14, "bold"))
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
            height=45, font=("Roboto", 15, "bold"), command=confirmar_cobro_mixto
        ).pack(fill="x", padx=35, pady=10)