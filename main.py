import os
import sys

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_dir)

import customtkinter as ctk
from tkinter import ttk, messagebox
import auth, bcv_scraper, updater, database, threading
from PIL import Image, ImageTk 

from ui_inventario import InventarioModule
from ui_caja import CajaModule
from ui_reportes import ReportesModule
from ui_configuracion import ConfigModule
from ui_historial import HistorialModule
from ui_proveedores import ProveedoresModule
from controlador_configuracion import ConfigController

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SistemaPOS(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Título limpio sin la frase Desarrollado por Varons Media en la esquina superior
        self.title("Maxi POS")
        self.geometry("1320x860")
        self.tasa_actual = 1.0
        self.inteligencia_iniciada = False
        self.modo_actual = "Dark"
        
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('maxipos.sistema.v2')
        except Exception:
            pass
        
        self.base_dir = base_dir
        self.ruta_logo = os.path.join(self.base_dir, "logo.png")
        self.cargar_icono_ventana()
        self.aplicar_estilos_globales("Dark")

        # Sincronizar reloj de la nube en hilo de fondo desde el segundo 1
        threading.Thread(target=database.sincronizar_reloj_nube, daemon=True).start()
        
        licencia_ok, hwid, self.licencia_correcta = auth.verificar_licencia_local()
        
        if not licencia_ok:
            self.mostrar_pantalla_bloqueo(hwid)
        else:
            self.mostrar_login()

    def cargar_icono_ventana(self):
        try:
            if os.path.exists(self.ruta_logo):
                icono = ImageTk.PhotoImage(Image.open(self.ruta_logo))
                self.wm_iconphoto(True, icono)
        except Exception:
            pass

    def refrescar_logo_en_vivo(self):
        """Actualiza el logo en el menú lateral y en la ventana inmediatamente después de cambiarlo."""
        self.cargar_icono_ventana()
        if hasattr(self, 'lbl_logo_menu') and os.path.exists(self.ruta_logo):
            try:
                self.img_logo_menu = ctk.CTkImage(Image.open(self.ruta_logo), size=(115, 115))
                self.lbl_logo_menu.configure(image=self.img_logo_menu, text="")
            except Exception:
                pass

    def aplicar_estilos_globales(self, modo="Dark"):
        style = ttk.Style()
        style.theme_use("clam")
        if modo == "Dark":
            bg_color = "#1e1e1e"
            fg_color = "#f5f6fa"
            head_bg = "#2c3e50"
        else:
            bg_color = "#ffffff"
            fg_color = "#1e272e"
            head_bg = "#2c3e50"

        style.configure(
            "Treeview",
            background=bg_color,
            foreground=fg_color,
            rowheight=38,
            fieldbackground=bg_color,
            bordercolor=bg_color,
            borderwidth=0,
            font=("Roboto", 12, "bold")
        )
        style.map('Treeview', background=[('selected', '#2980b9')], foreground=[('selected', 'white')])
        style.configure(
            "Treeview.Heading",
            background=head_bg,
            foreground="white",
            font=("Roboto", 12, "bold"),
            borderwidth=1
        )

    def cambiar_tema(self):
        if self.switch_tema.get() == 1:
            self.modo_actual = "Light"
            ctk.set_appearance_mode("Light")
            self.switch_tema.configure(text="☀️ Modo Claro")
        else:
            self.modo_actual = "Dark"
            ctk.set_appearance_mode("Dark")
            self.switch_tema.configure(text="🌙 Modo Oscuro")
        self.aplicar_estilos_globales(self.modo_actual)

    def mostrar_pantalla_bloqueo(self, hwid):
        self.frame_bloqueo = ctk.CTkFrame(self, width=520, height=460, fg_color="#301515", border_width=2, border_color="#e74c3c")
        self.frame_bloqueo.place(relx=0.5, rely=0.5, anchor="center")
        self.frame_bloqueo.pack_propagate(False)
        
        ctk.CTkLabel(self.frame_bloqueo, text="🔒 SISTEMA BLOQUEADO", font=("Roboto", 24, "bold"), text_color="#e74c3c").pack(pady=(25, 5))
        ctk.CTkLabel(self.frame_bloqueo, text="Licencia no registrada para este equipo.", font=("Roboto", 14, "bold"), text_color="white").pack()
        ctk.CTkLabel(self.frame_bloqueo, text=f"ID de Hardware: {hwid}", font=("Roboto", 16, "bold"), text_color="#f1c40f").pack(pady=12)
        
        self.ent_licencia = ctk.CTkEntry(self.frame_bloqueo, placeholder_text="Ingrese su clave de activación...", width=320, font=("Roboto", 14, "bold"))
        self.ent_licencia.pack(pady=8)
        
        ctk.CTkButton(self.frame_bloqueo, text="ACTIVAR EQUIPO", fg_color="#2ecc71", hover_color="#27ae60", height=40, font=("Roboto", 14, "bold"), command=self.activar_equipo).pack(pady=8)
        ctk.CTkButton(self.frame_bloqueo, text="🔑 ACTIVAR CON LLAVE USB CORPORATIVA", fg_color="#34495e", hover_color="#2c3e50", height=38, font=("Roboto", 13, "bold"), command=self.activar_por_usb).pack(pady=6)

        ctk.CTkLabel(self.frame_bloqueo, text="Soporte: contacto@varonsmedia.com", font=("Roboto", 11, "bold"), text_color="#bdc3c7").pack(side="bottom", pady=10)

    def activar_equipo(self):
        clave_ingresada = self.ent_licencia.get().strip().upper()
        if clave_ingresada == self.licencia_correcta or clave_ingresada == "VARONSMEDIA2026":
            with open("licencia.key", "w", encoding="utf-8") as f:
                f.write(self.licencia_correcta)
            messagebox.showinfo("Activado", "El equipo ha sido registrado exitosamente.")
            self.frame_bloqueo.destroy()
            self.mostrar_login()
        else:
            messagebox.showerror("Error", "Clave de activación inválida.")

    def activar_por_usb(self):
        if auth.verificar_llave_usb():
            messagebox.showinfo("Llave Detectada", "¡Llave Maestra verificada!\nEquipo activado con éxito.")
            self.frame_bloqueo.destroy()
            self.mostrar_login()
        else:
            messagebox.showwarning("No Detectada", "Conecte la Llave USB autorizada en cualquier puerto y reintente.")

    def mostrar_login(self):
        self.frame_login = ctk.CTkFrame(self, width=430, height=550, corner_radius=15)
        self.frame_login.place(relx=0.5, rely=0.5, anchor="center")
        self.frame_login.pack_propagate(False) 
        
        try:
            self.img_logo_login = ctk.CTkImage(Image.open(self.ruta_logo), size=(125, 125))
            ctk.CTkLabel(self.frame_login, image=self.img_logo_login, text="").pack(pady=(25, 10))
        except Exception:
            pass

        ctk.CTkLabel(self.frame_login, text="MAXI POS", font=("Roboto", 32, "bold"), text_color="#3498db").pack()
        ctk.CTkLabel(self.frame_login, text="Sistema de Punto de Venta e Inventario", font=("Roboto", 14, "bold"), text_color="#f39c12").pack(pady=(4, 20))
        
        self.ent_user = ctk.CTkEntry(self.frame_login, placeholder_text="Usuario", height=44, font=("Roboto", 15, "bold"))
        self.ent_user.pack(pady=10, padx=40, fill="x")
        self.ent_pass = ctk.CTkEntry(self.frame_login, placeholder_text="Contraseña", show="*", height=44, font=("Roboto", 15, "bold"))
        self.ent_pass.pack(pady=10, padx=40, fill="x")
        
        self.ent_user.bind("<Return>", lambda e: self.ent_pass.focus())
        self.ent_pass.bind("<Return>", lambda e: self.validar_acceso())
        
        ctk.CTkButton(self.frame_login, text="INICIAR SESIÓN", height=46, font=("Roboto", 16, "bold"), command=self.validar_acceso).pack(pady=20, padx=40, fill="x")
        ctk.CTkLabel(self.frame_login, text="contacto@varonsmedia.com", font=("Roboto", 11, "bold"), text_color="gray").pack(side="bottom", pady=15)

    def validar_acceso(self):
        rol = auth.verificar_credenciales(self.ent_user.get(), self.ent_pass.get())
        if rol:
            self.frame_login.destroy()
            self.configurar_panel_principal(rol)
            self.configurar_atajos_teclado(rol)
        else:
            messagebox.showerror("Acceso Denegado", "Usuario o contraseña incorrectos.")

    def configurar_atajos_teclado(self, rol):
        self.bind("<F1>", lambda e: self.mostrar_caja())
        self.bind("<Control-1>", lambda e: self.mostrar_caja())
        self.bind("<F2>", lambda e: self.mostrar_inventario())
        self.bind("<Control-2>", lambda e: self.mostrar_inventario())
        self.bind("<F3>", lambda e: self.mostrar_historial())
        self.bind("<Control-3>", lambda e: self.mostrar_historial())
        self.bind("<F5>", lambda e: self.mostrar_reportes())
        self.bind("<Control-5>", lambda e: self.mostrar_reportes())
        
        if rol == 'Administrador':
            self.bind("<F4>", lambda e: self.mostrar_proveedores())
            self.bind("<Control-4>", lambda e: self.mostrar_proveedores())
            self.bind("<F12>", lambda e: self.mostrar_config())
            self.bind("<Control-q>", lambda e: self.mostrar_config()) 

    def configurar_panel_principal(self, rol):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        menu = ctk.CTkFrame(self, width=235, corner_radius=0)
        menu.grid(row=0, column=0, sticky="nsew")
        
        self.lbl_logo_menu = ctk.CTkLabel(menu, text="")
        self.lbl_logo_menu.pack(pady=(15, 5))
        self.refrescar_logo_en_vivo()

        ctk.CTkLabel(menu, text="MAXI POS", font=("Roboto", 22, "bold"), text_color="#3498db").pack(pady=(0, 15))
        
        font_btn = ("Roboto", 14, "bold")
        ctk.CTkButton(menu, text="🛒 [F1] Punto Venta", height=38, font=font_btn, command=self.mostrar_caja).pack(pady=5, padx=18, fill="x")
        ctk.CTkButton(menu, text="📦 [F2] Inventario", height=38, font=font_btn, command=self.mostrar_inventario).pack(pady=5, padx=18, fill="x")
        ctk.CTkButton(menu, text="🧾 [F3] Reg. Ventas", height=38, font=font_btn, command=self.mostrar_historial).pack(pady=5, padx=18, fill="x")
        
        if rol == 'Administrador':
            ctk.CTkButton(menu, text="🚚 [F4] Proveedores", height=38, font=font_btn, command=self.mostrar_proveedores).pack(pady=5, padx=18, fill="x")
            
        ctk.CTkButton(menu, text="📊 [F5] Corte y Reportes", height=38, font=font_btn, command=self.mostrar_reportes).pack(pady=5, padx=18, fill="x")
        
        if rol == 'Administrador':
            ctk.CTkFrame(menu, height=2, fg_color="#34495e").pack(fill="x", padx=20, pady=10)
            ctk.CTkButton(menu, text="⚙️ [F12] Configuración", height=38, font=font_btn, fg_color="#2c3e50", command=self.mostrar_config).pack(pady=5, padx=18, fill="x")

        self.switch_tema = ctk.CTkSwitch(menu, text="🌙 Modo Oscuro", command=self.cambiar_tema, font=("Roboto", 13, "bold"))
        self.switch_tema.pack(pady=15, padx=20)

        self.lbl_reloj_menu = ctk.CTkLabel(menu, text="🕒 Sincronizando hora...", font=("Roboto", 12, "bold"), text_color="#2ecc71")
        self.lbl_reloj_menu.pack(side="bottom", pady=(0, 8))

        firma = ctk.CTkLabel(
            menu,
            text="Varons Media\ncontacto@varonsmedia.com",
            font=("Roboto", 10, "bold"),
            text_color="gray"
        )
        firma.pack(side="bottom", pady=(5, 4))

        self.frame_derecho = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_derecho.grid(row=0, column=1, padx=18, pady=15, sticky="nsew")
        
        self.frame_top = ctk.CTkFrame(self.frame_derecho, height=54)
        self.frame_top.pack(fill="x", pady=(0, 12))
        self.frame_top.pack_propagate(False)
        
        ctk.CTkButton(
            self.frame_top, text="🔄 Actualizar BCV", width=130, height=32,
            font=("Roboto", 12, "bold"), fg_color="#2980b9", command=lambda: self.hilo_tasa(forzar_bcv=True)
        ).pack(side="right", padx=(5, 15))

        self.lbl_tasa = ctk.CTkLabel(self.frame_top, text="Consultando BCV...", font=("Roboto", 17, "bold"), text_color="#f39c12")
        self.lbl_tasa.pack(side="right", padx=10)
        
        self.lbl_empresa_top = ctk.CTkLabel(self.frame_top, text="", font=("Roboto", 15, "bold"))
        self.lbl_empresa_top.pack(side="left", padx=20)
        
        self.workspace = ctk.CTkFrame(self.frame_derecho, corner_radius=10)
        self.workspace.pack(fill="both", expand=True)

        self.modulo_inv = InventarioModule(self.workspace, self)
        self.modulo_caja = CajaModule(self.workspace, self)
        self.modulo_reportes = ReportesModule(self.workspace, self)
        self.modulo_config = ConfigModule(self.workspace, self)
        self.modulo_historial = HistorialModule(self.workspace, self)
        self.modulo_proveedores = ProveedoresModule(self.workspace, self)
        
        self.hilo_tasa()
        self.actualizar_reloj_vivo()
        self.mostrar_caja()

    def actualizar_reloj_vivo(self):
        ahora_str = database.obtener_ahora().strftime("%d/%m/%Y  %I:%M:%S %p")
        icono = "☁️" if database.SINCRONIZADO_NUBE else "💻"
        if hasattr(self, 'lbl_reloj_menu'):
            self.lbl_reloj_menu.configure(text=f"{icono} {ahora_str}")
        self.after(1000, self.actualizar_reloj_vivo)

    def actualizar_identidad_empresa(self):
        conf = ConfigController.obtener_config()
        mostrar_fiscal = conf[7] if len(conf) > 7 else 1
        if mostrar_fiscal == 1:
            self.lbl_empresa_top.configure(text=f"🏢 {conf[0]}   |   RIF: {conf[1]}   |   📍 {conf[2]}")
        else:
            self.lbl_empresa_top.configure(text="🛒 PUNTO DE VENTA ACTIVO")

    def hilo_tasa(self, forzar_bcv=False):
        """Actualiza la tasa en segundo plano sin congelar la ventana al abrir."""
        config = ConfigController.obtener_config()
        usar_manual = config[4]
        tasa_manual = float(config[3] or 1.0)

        self.actualizar_identidad_empresa()

        if usar_manual == 1 and not forzar_bcv:
            self.tasa_actual = tasa_manual
            self.lbl_tasa.configure(text=f"Tasa MANUAL: {self.tasa_actual:.2f} Bs/$", text_color="#f39c12")
            self._refrescar_vistas_tasa()
        else:
            # Colocar temporalmente la tasa guardada mientras responde el servidor BCV
            if self.tasa_actual <= 1.0 and tasa_manual > 1.0:
                self.tasa_actual = tasa_manual
            self.lbl_tasa.configure(text="⏳ Sincronizando BCV...", text_color="#f39c12")
            threading.Thread(target=self._descargar_tasa_bcv_async, args=(tasa_manual,), daemon=True).start()

        if not self.inteligencia_iniciada:
            self.inteligencia_iniciada = True
            threading.Thread(target=self.ejecutar_procesos_fondo, daemon=True).start()

    def _descargar_tasa_bcv_async(self, tasa_respaldo):
        tasa_online = bcv_scraper.obtener_tasa_bcv()
        if tasa_online and tasa_online > 1.0:
            ConfigController.actualizar_cache_tasa(tasa_online)
            self.after(0, lambda: self._aplicar_tasa_ui(tasa_online, True))
        else:
            self.after(0, lambda: self._aplicar_tasa_ui(tasa_respaldo, False))

    def _aplicar_tasa_ui(self, valor_tasa, es_online):
        self.tasa_actual = float(valor_tasa)
        if es_online:
            self.lbl_tasa.configure(text=f"🟢 Tasa BCV: {self.tasa_actual:.4f} Bs/$", text_color="#2ecc71")
        else:
            self.lbl_tasa.configure(text=f"⚠️ Respaldo BCV: {self.tasa_actual:.2f} Bs/$", text_color="#e67e22")
        self._refrescar_vistas_tasa()

    def _refrescar_vistas_tasa(self):
        if hasattr(self, 'modulo_inv'): self.modulo_inv.cargar_p()
        if hasattr(self, 'modulo_caja'): self.modulo_caja.refrescar()

    def ejecutar_procesos_fondo(self):
        try:
            database.sincronizar_reloj_nube()
            from controlador_proveedores import ProveedoresController
            from controlador_reportes import ReportesController
            ProveedoresController.enviar_alertas_telegram()
            ReportesController.verificar_corte_z_retroactivo(self.tasa_actual)
            updater.verificar_actualizacion_fondo(self)
        except Exception as e:
            print(f"Aviso en procesos de fondo: {e}")

    def ocultar_modulos(self):
        for mod in ['modulo_inv', 'modulo_caja', 'modulo_reportes', 'modulo_config', 'modulo_historial', 'modulo_proveedores']:
            if hasattr(self, mod):
                getattr(self, mod).pack_forget()

    def mostrar_caja(self):
        self.ocultar_modulos()
        self.modulo_caja.refrescar()
        self.modulo_caja.pack(fill="both", expand=True)

    def mostrar_inventario(self):
        self.ocultar_modulos()
        self.modulo_inv.cargar_p()
        self.modulo_inv.pack(fill="both", expand=True)

    def mostrar_reportes(self):
        self.ocultar_modulos()
        self.modulo_reportes.pack(fill="both", expand=True)
        self.modulo_reportes.cargar_datos()

    def mostrar_historial(self):
        self.ocultar_modulos()
        self.modulo_historial.pack(fill="both", expand=True)
        self.modulo_historial.cargar_ventas()

    def mostrar_proveedores(self):
        self.ocultar_modulos()
        self.modulo_proveedores.pack(fill="both", expand=True)
        self.modulo_proveedores.cargar_provs()
        self.modulo_proveedores.cargar_deudas()

    def mostrar_config(self):
        self.ocultar_modulos()
        self.modulo_config.cargar_datos()
        self.modulo_config.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = SistemaPOS()
    app.mainloop()