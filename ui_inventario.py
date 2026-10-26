import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
import os
import database

class InventarioModule(ctk.CTkFrame):
    def __init__(self, master, app_parent):
        super().__init__(master, fg_color="transparent")
        self.app_parent = app_parent
        self.id_sel = None
        self.img_path = ""
        self.vcmd_num = (self.register(self.validar_entrada_numerica), '%P')
        self.setup_ui()

    def validar_entrada_numerica(self, texto_nuevo):
        if texto_nuevo == "":
            return True
        texto_normalizado = texto_nuevo.replace(',', '.')
        if texto_normalizado.count('.') > 1:
            return False
        for p in texto_normalizado.split('.'):
            if p != "" and not p.isdigit():
                return False
        return True

    def setup_ui(self):
        self.ent_bus = ctk.CTkEntry(self, placeholder_text="🔍 BUSCAR PRODUCTO POR CÓDIGO O NOMBRE...", width=420)
        self.ent_bus.pack(pady=(10, 15), padx=20, anchor="w")
        self.ent_bus.bind("<KeyRelease>", self.buscar_p)

        f_main = ctk.CTkFrame(self, fg_color="transparent")
        f_main.pack(fill="x", padx=20)

        f_form = ctk.CTkFrame(f_main, fg_color="transparent")
        f_form.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(f_form, text="Cód de Barras:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.e_cod = ctk.CTkEntry(f_form, width=150)
        self.e_cod.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(f_form, text="Nombre del Producto:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.e_nom = ctk.CTkEntry(f_form, width=250)
        self.e_nom.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(f_form, text="Categoría:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.cb_cat = ctk.CTkComboBox(f_form, values=["Víveres", "Charcutería", "Carnicería", "Lácteos", "Bebidas", "Otros"], width=150)
        self.cb_cat.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(f_form, text="U. Medida:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.cb_um = ctk.CTkComboBox(f_form, values=["Unidad", "KG", "LITRO", "GR"], width=150)
        self.cb_um.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(f_form, text="Costo Compra $:", text_color="#f39c12", font=("Roboto", 12, "bold")).grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.e_costo_usd = ctk.CTkEntry(f_form, width=150, validate="key", validatecommand=self.vcmd_num)
        self.e_costo_usd.grid(row=2, column=1, padx=5, pady=5)
        self.e_costo_usd.bind("<KeyRelease>", self.calc_todo)

        ctk.CTkLabel(f_form, text="Costo en Bs:", text_color="#f39c12").grid(row=2, column=2, padx=5, pady=5, sticky="e")
        self.e_costo_bs = ctk.CTkEntry(f_form, width=150, state="disabled")
        self.e_costo_bs.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(f_form, text="Precio Venta $:", text_color="#3498db", font=("Roboto", 12, "bold")).grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.e_venta_usd = ctk.CTkEntry(f_form, width=150, validate="key", validatecommand=self.vcmd_num)
        self.e_venta_usd.grid(row=3, column=1, padx=5, pady=5)
        self.e_venta_usd.bind("<KeyRelease>", self.calc_todo)

        ctk.CTkLabel(f_form, text="Precio Venta Bs:", text_color="#2ecc71", font=("Roboto", 12, "bold")).grid(row=3, column=2, padx=5, pady=5, sticky="e")
        self.e_venta_bs = ctk.CTkEntry(f_form, width=150, state="disabled")
        self.e_venta_bs.grid(row=3, column=3, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(f_form, text="Precio Mayor $:", text_color="#9b59b6", font=("Roboto", 12, "bold")).grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.e_mayor_usd = ctk.CTkEntry(f_form, width=150, validate="key", validatecommand=self.vcmd_num)
        self.e_mayor_usd.grid(row=4, column=1, padx=5, pady=5)
        self.e_mayor_usd.bind("<KeyRelease>", self.calc_todo)

        ctk.CTkLabel(f_form, text="Precio Mayor Bs:", text_color="#8e44ad").grid(row=4, column=2, padx=5, pady=5, sticky="e")
        self.e_mayor_bs = ctk.CTkEntry(f_form, width=150, state="disabled")
        self.e_mayor_bs.grid(row=4, column=3, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(f_form, text="Stock Actual:").grid(row=4, column=4, padx=5, pady=5, sticky="e")
        self.e_stock = ctk.CTkEntry(f_form, width=100, validate="key", validatecommand=self.vcmd_num)
        self.e_stock.grid(row=4, column=5, padx=5, pady=5)

        self.frame_asesor = ctk.CTkFrame(f_form, corner_radius=8)
        self.frame_asesor.grid(row=5, column=0, columnspan=6, pady=12, padx=5, sticky="ew")
        
        self.lbl_margen = ctk.CTkLabel(
            self.frame_asesor,
            text="💡 Asistente de Precios: Ingrese el Costo ($) para ver el precio sugerido y su ganancia por unidad.",
            font=("Roboto", 12, "bold"),
            text_color="#3498db",
            justify="left"
        )
        self.lbl_margen.pack(pady=8, padx=12, anchor="w")

        f_img = ctk.CTkFrame(f_main, width=190, height=190)
        f_img.pack(side="right", padx=20, pady=10)
        f_img.pack_propagate(False)

        self.lbl_img = ctk.CTkLabel(f_img, text="SIN IMAGEN", text_color="gray", font=("Roboto", 13))
        self.lbl_img.pack(expand=True, fill="both")

        ctk.CTkButton(self, text="📸 Seleccionar Foto", width=150, command=self.sel_foto).pack(pady=4)

        f_btns = ctk.CTkFrame(self, fg_color="transparent")
        f_btns.pack(pady=10)

        ctk.CTkButton(f_btns, text="✨ NUEVO / LIMPIAR", fg_color="#7f8c8d", hover_color="#95a5a6", command=self.limpiar_campos).pack(side="left", padx=10)
        ctk.CTkButton(f_btns, text="💾 GUARDAR NUEVO", fg_color="#2ecc71", hover_color="#27ae60", command=self.guardar_p).pack(side="left", padx=10)
        ctk.CTkButton(f_btns, text="🔄 ACTUALIZAR", fg_color="#3498db", hover_color="#2980b9", command=self.actualizar_p).pack(side="left", padx=10)
        ctk.CTkButton(f_btns, text="🗑️ ELIMINAR", fg_color="#e74c3c", hover_color="#c0392b", command=self.eliminar_p).pack(side="left", padx=10)

        f_tabla = ctk.CTkFrame(self, fg_color="transparent")
        f_tabla.pack(fill="both", expand=True, padx=20, pady=10)

        scroll_y = ttk.Scrollbar(f_tabla, orient="vertical")
        scroll_x = ttk.Scrollbar(f_tabla, orient="horizontal")

        self.tabla = ttk.Treeview(f_tabla, columns=("ID", "C", "N", "CAT", "UM", "C$", "V$", "VBS", "S"), show="headings", yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.configure(command=self.tabla.yview)
        scroll_x.configure(command=self.tabla.xview)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tabla.pack(fill="both", expand=True)

        encabezados = [("ID", "ID", 30), ("C", "CÓDIGO", 80), ("N", "NOMBRE", 200), ("CAT", "CATEGORÍA", 100), ("UM", "U.M", 60), ("C$", "COSTO", 80), ("V$", "VENTA $", 80), ("VBS", "VENTA BS", 100), ("S", "STOCK", 60)]
        for col, tex, anc in encabezados:
            self.tabla.heading(col, text=tex)
            self.tabla.column(col, width=anc, anchor="center")
        self.tabla.column("N", anchor="w")

        self.tabla.bind("<<TreeviewSelect>>", self.on_select)
        self.cargar_p()

    def set_entry(self, entry, text):
        state = entry.cget('state')
        if state == 'disabled':
            entry.configure(state='normal')
        entry.delete(0, 'end')
        entry.insert(0, str(text))
        if state == 'disabled':
            entry.configure(state='disabled')

    def get_val(self, entry):
        try:
            return float(entry.get().replace(',', '.'))
        except Exception:
            return 0.0

    def calc_todo(self, event=None):
        tasa = self.app_parent.tasa_actual
        c_usd = self.get_val(self.e_costo_usd)
        v_usd = self.get_val(self.e_venta_usd)
        m_usd = self.get_val(self.e_mayor_usd)

        self.set_entry(self.e_costo_bs, f"{c_usd * tasa:.2f}")
        self.set_entry(self.e_venta_bs, f"{v_usd * tasa:.2f}")
        self.set_entry(self.e_mayor_bs, f"{m_usd * tasa:.2f}")

        if c_usd <= 0:
            self.lbl_margen.configure(
                text="💡 Asistente de Precios: Ingrese el Costo ($) para calcular sugerencias de venta y ganancia.",
                text_color="#3498db"
            )
            return

        precio_sugerido = c_usd / 0.70
        ganancia_usd = v_usd - c_usd

        if v_usd <= 0:
            self.lbl_margen.configure(
                text=f"💡 Sugerencia comercial: Para obtener un 30% de margen, puede venderlo en ${precio_sugerido:.2f} (Bs. {precio_sugerido * tasa:.2f}).",
                text_color="#f39c12"
            )
        elif v_usd <= c_usd:
            self.lbl_margen.configure(
                text=f"ℹ️ Atención: El precio de venta (${v_usd:.2f}) no cubre el costo (${c_usd:.2f}). Sugerido: ${precio_sugerido:.2f}.",
                text_color="#e67e22"
            )
        else:
            margen = (ganancia_usd / v_usd) * 100
            if margen < 15:
                mensaje = f"📊 Ganancia: +${ganancia_usd:.2f}/ud ({margen:.1f}%) — Margen ajustado, ideal para alta rotación. (Sugerido 30%: ${precio_sugerido:.2f})"
                color = "#f39c12"
            elif margen < 30:
                mensaje = f"✅ Ganancia: +${ganancia_usd:.2f}/ud ({margen:.1f}%) — Margen comercial equilibrado y competitivo."
                color = "#2ecc71"
            else:
                mensaje = f"⭐ Ganancia: +${ganancia_usd:.2f}/ud ({margen:.1f}%) — Excelente rentabilidad para tu negocio."
                color = "#2ecc71"
            self.lbl_margen.configure(text=mensaje, text_color=color)

    def validar_formulario(self):
        cod = self.e_cod.get().strip()
        nom = self.e_nom.get().strip()
        c_usd = self.get_val(self.e_costo_usd)
        v_usd = self.get_val(self.e_venta_usd)

        if not cod or not nom:
            messagebox.showwarning("Datos Incompletos", "Por favor, ingrese el Código y el Nombre del producto.")
            return False
        if nom.replace(" ", "").isdigit():
            messagebox.showwarning("Nombre Inválido", "El nombre del producto debe describir el artículo (no puede contener solo números).")
            return False
        if v_usd <= 0:
            messagebox.showwarning("Precio Requerido", "El Precio de Venta ($) debe ser mayor a 0.00.")
            return False
        if v_usd < c_usd:
            confirmar = messagebox.askyesno(
                "Confirmar Precio",
                f"El precio de venta (${v_usd:.2f}) es menor al costo de compra (${c_usd:.2f}).\n¿Desea guardarlo de todas formas?"
            )
            if not confirmar:
                return False
        return True

    def limpiar_campos(self):
        self.id_sel = None
        for entry in [self.e_cod, self.e_nom, self.e_costo_usd, self.e_venta_usd, self.e_mayor_usd, self.e_stock]:
            self.set_entry(entry, "")
        self.calc_todo()
        self.limpiar_imagen()
        seleccion = self.tabla.selection()
        if seleccion:
            self.tabla.selection_remove(seleccion[0])

    def limpiar_imagen(self):
        self.img_path = ""
        self.lbl_img.configure(image="", text="SIN IMAGEN")

    def cargar_imagen_visual(self, ruta):
        if ruta and os.path.exists(ruta):
            try:
                img = ctk.CTkImage(Image.open(ruta), size=(170, 170))
                self.lbl_img.configure(image=img, text="")
                self.img_path = ruta
            except Exception:
                self.limpiar_imagen()
        else:
            self.limpiar_imagen()

    def sel_foto(self):
        p = filedialog.askopenfilename(title="Seleccionar Foto", filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if p:
            self.cargar_imagen_visual(p)

    def cargar_p(self, filtro=""):
        for i in self.tabla.get_children():
            self.tabla.delete(i)
        conn = database.conectar_db()
        c = conn.cursor()
        if filtro:
            c.execute("SELECT id, codigo_barras, nombre, categoria, unidad_medida, costo_usd, precio_venta_usd, stock_actual FROM Productos WHERE codigo_barras LIKE ? OR nombre LIKE ?", (f"%{filtro}%", f"%{filtro}%"))
        else:
            c.execute("SELECT id, codigo_barras, nombre, categoria, unidad_medida, costo_usd, precio_venta_usd, stock_actual FROM Productos")
        
        tasa = self.app_parent.tasa_actual
        for p in c.fetchall():
            v_bs = p[6] * tasa
            self.tabla.insert("", "end", values=(p[0], p[1], p[2], p[3], p[4], f"${p[5]:.2f}", f"${p[6]:.2f}", f"Bs. {v_bs:.2f}", p[7]))
        conn.close()

    def buscar_p(self, e):
        self.cargar_p(self.ent_bus.get())

    def on_select(self, e):
        s = self.tabla.selection()
        if s:
            val = self.tabla.item(s[0])['values']
            self.id_sel = val[0]
            
            conn = database.conectar_db()
            c = conn.cursor()
            c.execute("SELECT codigo_barras, nombre, categoria, unidad_medida, costo_usd, precio_venta_usd, precio_mayor_usd, stock_actual, imagen_path FROM Productos WHERE id=?", (self.id_sel,))
            row = c.fetchone()
            conn.close()
            
            if row:
                self.set_entry(self.e_cod, row[0])
                self.set_entry(self.e_nom, row[1])
                self.cb_cat.set(row[2])
                self.cb_um.set(row[3])
                self.set_entry(self.e_costo_usd, row[4])
                self.set_entry(self.e_venta_usd, row[5])
                self.set_entry(self.e_mayor_usd, row[6])
                self.set_entry(self.e_stock, row[7])
                self.calc_todo()
                
                if row[8]:
                    self.cargar_imagen_visual(row[8])
                else:
                    self.limpiar_imagen()

    def guardar_p(self):
        if not self.validar_formulario():
            return
        conn = database.conectar_db()
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO Productos (codigo_barras, nombre, categoria, unidad_medida, costo_usd, precio_venta_usd, precio_mayor_usd, stock_actual, imagen_path) VALUES (?,?,?,?,?,?,?,?,?)",
                (self.e_cod.get().strip(), self.e_nom.get().strip().upper(), self.cb_cat.get(), self.cb_um.get(), self.get_val(self.e_costo_usd), self.get_val(self.e_venta_usd), self.get_val(self.e_mayor_usd), self.get_val(self.e_stock), self.img_path)
            )
            conn.commit()
            messagebox.showinfo("Guardado", "Producto registrado exitosamente.")
            self.limpiar_campos() 
            self.cargar_p()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el producto:\n{e}")
        finally:
            conn.close()

    def actualizar_p(self):
        if not self.id_sel:
            return messagebox.showwarning("Aviso", "Seleccione un producto de la tabla primero.")
        if not self.validar_formulario():
            return
        conn = database.conectar_db()
        c = conn.cursor()
        try:
            c.execute(
                "UPDATE Productos SET codigo_barras=?, nombre=?, categoria=?, unidad_medida=?, costo_usd=?, precio_venta_usd=?, precio_mayor_usd=?, stock_actual=?, imagen_path=? WHERE id=?",
                (self.e_cod.get().strip(), self.e_nom.get().strip().upper(), self.cb_cat.get(), self.cb_um.get(), self.get_val(self.e_costo_usd), self.get_val(self.e_venta_usd), self.get_val(self.e_mayor_usd), self.get_val(self.e_stock), self.img_path, self.id_sel)
            )
            conn.commit()
            messagebox.showinfo("Actualizado", "Datos del producto actualizados exitosamente.")
            self.cargar_p()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar:\n{e}")
        finally:
            conn.close()

    def eliminar_p(self):
        if not self.id_sel:
            return messagebox.showwarning("Aviso", "Seleccione un producto de la tabla primero.")
        if messagebox.askyesno("Confirmar", "¿Eliminar producto del inventario?"):
            conn = database.conectar_db()
            c = conn.cursor()
            c.execute("DELETE FROM Productos WHERE id=?", (self.id_sel,))
            conn.commit()
            conn.close()
            self.limpiar_campos()
            self.cargar_p()