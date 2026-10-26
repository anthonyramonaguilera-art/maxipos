import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
import os
from controlador_configuracion import ConfigController

class ConfigModule(ctk.CTkFrame):
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
        f_main = ctk.CTkFrame(self, fg_color="transparent")
        f_main.pack(fill="both", expand=True, padx=15, pady=10)
        f_main.grid_columnconfigure(0, weight=5)
        f_main.grid_columnconfigure(1, weight=5)
        f_main.grid_rowconfigure(0, weight=1)

        # COLUMNA IZQUIERDA: Empresa, Logo, Tasa BCV, Balanza y Telegram
        f_izq = ctk.CTkFrame(f_main, corner_radius=12)
        f_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=5)

        ctk.CTkLabel(f_izq, text="🏢 DATOS DE EMPRESA, LOGO Y BALANZA", font=("Roboto", 16, "bold"), text_color="#3498db").pack(pady=(12, 8))

        f_form = ctk.CTkFrame(f_izq, fg_color="transparent")
        f_form.pack(pady=4, padx=10)

        lbl_font = ("Roboto", 13, "bold")
        ent_font = ("Roboto", 13, "bold")

        ctk.CTkLabel(f_form, text="Nombre del Negocio:", font=lbl_font).grid(row=0, column=0, padx=8, pady=5, sticky="e")
        self.e_nom = ctk.CTkEntry(f_form, width=240, font=ent_font)
        self.e_nom.grid(row=0, column=1, padx=8, pady=5)

        ctk.CTkLabel(f_form, text="RIF / Documento:", font=lbl_font).grid(row=1, column=0, padx=8, pady=5, sticky="e")
        self.e_rif = ctk.CTkEntry(f_form, width=240, font=ent_font)
        self.e_rif.grid(row=1, column=1, padx=8, pady=5)

        ctk.CTkLabel(f_form, text="Dirección / Ubicación:", font=lbl_font).grid(row=2, column=0, padx=8, pady=5, sticky="e")
        self.e_dir = ctk.CTkEntry(f_form, width=240, font=ent_font)
        self.e_dir.grid(row=2, column=1, padx=8, pady=5)

        self.sw_mostrar_fiscal = ctk.CTkSwitch(
            f_form, text="Mostrar Nombre, RIF y Ubicación en pantalla y tickets", font=("Roboto", 12, "bold")
        )
        self.sw_mostrar_fiscal.grid(row=3, column=0, columnspan=2, pady=6)

        ctk.CTkLabel(f_form, text="Tasa Manual Respaldo (Bs/$):", font=lbl_font).grid(row=4, column=0, padx=8, pady=5, sticky="e")
        self.e_tasa = ctk.CTkEntry(f_form, width=240, font=ent_font, validate="key", validatecommand=self.vcmd_num)
        self.e_tasa.grid(row=4, column=1, padx=8, pady=5)

        self.sw_manual = ctk.CTkSwitch(f_form, text="Forzar Tasa Manual (Desactivar BCV Automático)", font=("Roboto", 12, "bold"))
        self.sw_manual.grid(row=5, column=0, columnspan=2, pady=6)

        ctk.CTkLabel(f_form, text="Puerto Balanza (ej. COM3):", font=lbl_font).grid(row=6, column=0, padx=8, pady=5, sticky="e")
        self.e_com = ctk.CTkEntry(f_form, width=240, font=ent_font)
        self.e_com.grid(row=6, column=1, padx=8, pady=5)

        ctk.CTkLabel(f_form, text="Telegram Bot Token:", font=lbl_font).grid(row=7, column=0, padx=8, pady=5, sticky="e")
        self.e_tg_token = ctk.CTkEntry(f_form, width=240, font=ent_font, placeholder_text="Token de @BotFather")
        self.e_tg_token.grid(row=7, column=1, padx=8, pady=5)

        ctk.CTkLabel(f_form, text="Telegram Chat ID:", font=lbl_font).grid(row=8, column=0, padx=8, pady=5, sticky="e")
        self.e_tg_chat = ctk.CTkEntry(f_form, width=240, font=ent_font, placeholder_text="ID numérico de Telegram")
        self.e_tg_chat.grid(row=8, column=1, padx=8, pady=5)

        f_botones_cfg = ctk.CTkFrame(f_izq, fg_color="transparent")
        f_botones_cfg.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            f_botones_cfg, text="🖼️ CAMBIAR LOGO DEL PROGRAMA",
            fg_color="#8e44ad", hover_color="#9b59b6", height=38, font=("Roboto", 13, "bold"),
            command=self.cambiar_logo_sistema
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            f_botones_cfg, text="💾 GUARDAR PARÁMETROS GENERALES",
            fg_color="#2ecc71", hover_color="#27ae60", height=42, font=("Roboto", 14, "bold"),
            command=self.guardar
        ).pack(fill="x", pady=4)

        # COLUMNA DERECHA: Gestión de Usuarios y Contraseñas
        f_der = ctk.CTkFrame(f_main, corner_radius=12)
        f_der.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=5)

        ctk.CTkLabel(f_der, text="👤 GESTIÓN DE USUARIOS Y CONTRASEÑAS", font=("Roboto", 16, "bold"), text_color="#f39c12").pack(pady=(12, 8))

        f_uform = ctk.CTkFrame(f_der, fg_color="transparent")
        f_uform.pack(pady=4, padx=10)

        ctk.CTkLabel(f_uform, text="Nombre de Usuario:", font=lbl_font).grid(row=0, column=0, padx=6, pady=5, sticky="e")
        self.e_user_nom = ctk.CTkEntry(f_uform, width=200, font=ent_font, placeholder_text="Ej. admin o cajero1")
        self.e_user_nom.grid(row=0, column=1, padx=6, pady=5)

        ctk.CTkLabel(f_uform, text="Nueva Contraseña:", font=lbl_font).grid(row=1, column=0, padx=6, pady=5, sticky="e")
        self.e_user_pass = ctk.CTkEntry(f_uform, width=200, font=ent_font, placeholder_text="Escriba la clave...")
        self.e_user_pass.grid(row=1, column=1, padx=6, pady=5)

        ctk.CTkLabel(f_uform, text="Rol de Acceso:", font=lbl_font).grid(row=2, column=0, padx=6, pady=5, sticky="e")
        self.cb_user_rol = ctk.CTkComboBox(f_uform, values=["Administrador", "Cajero"], width=200, font=ent_font)
        self.cb_user_rol.grid(row=2, column=1, padx=6, pady=5)

        f_ubtns = ctk.CTkFrame(f_der, fg_color="transparent")
        f_ubtns.pack(fill="x", padx=25, pady=8)

        ctk.CTkButton(
            f_ubtns, text="➕ Crear / Actualizar Clave", fg_color="#2980b9", hover_color="#3498db",
            height=38, font=("Roboto", 13, "bold"), command=self.guardar_usuario_ui
        ).pack(side="left", fill="x", expand=True, padx=4)

        ctk.CTkButton(
            f_ubtns, text="🗑️ Eliminar Usuario", fg_color="#e74c3c", hover_color="#c0392b",
            height=38, font=("Roboto", 13, "bold"), command=self.eliminar_usuario_ui
        ).pack(side="right", padx=4)

        self.tabla_users = ttk.Treeview(f_der, columns=("ID", "USER", "ROL", "ESTADO"), show="headings", height=8)
        for col, tit, anc in [("ID", "ID", 40), ("USER", "USUARIO", 150), ("ROL", "ROL", 130), ("ESTADO", "ESTADO", 90)]:
            self.tabla_users.heading(col, text=tit)
            self.tabla_users.column(col, width=anc, anchor="center")
        self.tabla_users.pack(fill="both", expand=True, padx=15, pady=8)
        self.tabla_users.bind("<<TreeviewSelect>>", self.seleccionar_usuario_tabla)

        ctk.CTkLabel(
            f_der,
            text="Desarrollado por Varons Media  |  contacto@varonsmedia.com",
            font=("Roboto", 11, "bold"), text_color="gray"
        ).pack(side="bottom", pady=8)

    def cambiar_logo_sistema(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar Nuevo Logo del Negocio",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.ico")]
        )
        if archivo:
            try:
                img = Image.open(archivo).convert("RGBA")
                img.thumbnail((400, 400))
                img.save(self.app_parent.ruta_logo, "PNG")
                self.app_parent.refrescar_logo_en_vivo()
                messagebox.showinfo("Logo Actualizado", "¡El logo del sistema ha sido actualizado exitosamente!")
            except Exception as e:
                messagebox.showerror("Error al cambiar logo", f"No se pudo procesar la imagen:\n{e}")

    def cargar_datos(self):
        conf = ConfigController.obtener_config()
        self.e_nom.delete(0, 'end'); self.e_nom.insert(0, conf[0])
        self.e_rif.delete(0, 'end'); self.e_rif.insert(0, conf[1])
        self.e_dir.delete(0, 'end'); self.e_dir.insert(0, conf[2])
        self.e_tasa.delete(0, 'end'); self.e_tasa.insert(0, str(conf[3]))

        if conf[4] == 1:
            self.sw_manual.select()
        else:
            self.sw_manual.deselect()

        self.e_tg_token.delete(0, 'end'); self.e_tg_token.insert(0, conf[5] if len(conf) > 5 else "")
        self.e_tg_chat.delete(0, 'end'); self.e_tg_chat.insert(0, conf[6] if len(conf) > 6 else "")

        mostrar_fiscal = conf[7] if len(conf) > 7 else 1
        if mostrar_fiscal == 1:
            self.sw_mostrar_fiscal.select()
        else:
            self.sw_mostrar_fiscal.deselect()

        puerto = conf[8] if len(conf) > 8 else "COM3"
        self.e_com.delete(0, 'end'); self.e_com.insert(0, puerto)

        self.cargar_tabla_usuarios()

    def cargar_tabla_usuarios(self):
        for i in self.tabla_users.get_children():
            self.tabla_users.delete(i)
        for u in ConfigController.listar_usuarios():
            self.tabla_users.insert("", "end", values=u)

    def seleccionar_usuario_tabla(self, event=None):
        sel = self.tabla_users.selection()
        if sel:
            vals = self.tabla_users.item(sel[0])['values']
            self.e_user_nom.delete(0, 'end')
            self.e_user_nom.insert(0, vals[1])
            self.cb_user_rol.set(vals[2])
            self.e_user_pass.delete(0, 'end')

    def guardar_usuario_ui(self):
        ok, msg = ConfigController.guardar_usuario(
            self.e_user_nom.get(),
            self.e_user_pass.get(),
            self.cb_user_rol.get()
        )
        if ok:
            self.e_user_nom.delete(0, 'end')
            self.e_user_pass.delete(0, 'end')
            self.cargar_tabla_usuarios()
            messagebox.showinfo("Usuarios", msg)
        else:
            messagebox.showwarning("Aviso", msg)

    def eliminar_usuario_ui(self):
        sel = self.tabla_users.selection()
        if not sel:
            return messagebox.showwarning("Aviso", "Seleccione un usuario de la tabla.")
        vals = self.tabla_users.item(sel[0])['values']
        if messagebox.askyesno("Confirmar", f"¿Desea eliminar al usuario '{vals[1]}'?"):
            ok, msg = ConfigController.eliminar_usuario(vals[0])
            if ok:
                self.cargar_tabla_usuarios()
                messagebox.showinfo("Eliminado", msg)
            else:
                messagebox.showwarning("Acción No Permitida", msg)

    def guardar(self):
        try:
            tasa = float(self.e_tasa.get().replace(',', '.'))
            if tasa <= 0:
                tasa = 1.0
        except Exception:
            tasa = 1.0

        mostrar_fiscal = 1 if self.sw_mostrar_fiscal.get() == 1 else 0

        ConfigController.guardar_config(
            self.e_nom.get(),
            self.e_rif.get(),
            self.e_dir.get(),
            tasa,
            self.sw_manual.get(),
            self.e_tg_token.get(),
            self.e_tg_chat.get(),
            mostrar_fiscal,
            self.e_com.get()
        )
        self.app_parent.hilo_tasa()
        messagebox.showinfo("Configuración Guardada", "Los parámetros de la empresa, tasa y balanza han sido actualizados.")