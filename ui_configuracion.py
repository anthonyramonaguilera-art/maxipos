import customtkinter as ctk
from tkinter import messagebox
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
        f_card = ctk.CTkFrame(self, width=650, corner_radius=12)
        f_card.pack(pady=15, padx=20, fill="both", expand=True)

        ctk.CTkLabel(f_card, text="⚙️ CONFIGURACIÓN DE EMPRESA Y PARÁMETROS", font=("Roboto", 18, "bold")).pack(pady=(15, 10))

        f_form = ctk.CTkFrame(f_card, fg_color="transparent")
        f_form.pack(pady=5)

        ctk.CTkLabel(f_form, text="Nombre del Negocio:").grid(row=0, column=0, padx=10, pady=6, sticky="e")
        self.e_nom = ctk.CTkEntry(f_form, width=280)
        self.e_nom.grid(row=0, column=1, padx=10, pady=6)

        ctk.CTkLabel(f_form, text="RIF / Documento:").grid(row=1, column=0, padx=10, pady=6, sticky="e")
        self.e_rif = ctk.CTkEntry(f_form, width=280)
        self.e_rif.grid(row=1, column=1, padx=10, pady=6)

        ctk.CTkLabel(f_form, text="Dirección Fiscal:").grid(row=2, column=0, padx=10, pady=6, sticky="e")
        self.e_dir = ctk.CTkEntry(f_form, width=280)
        self.e_dir.grid(row=2, column=1, padx=10, pady=6)

        self.sw_mostrar_fiscal = ctk.CTkSwitch(
            f_form,
            text="Mostrar Nombre, RIF y Ubicación en barra superior y tickets",
            font=("Roboto", 12, "bold")
        )
        self.sw_mostrar_fiscal.grid(row=3, column=0, columnspan=2, pady=8)

        ctk.CTkLabel(f_form, text="Tasa Manual Respaldo (Bs/$):").grid(row=4, column=0, padx=10, pady=6, sticky="e")
        self.e_tasa = ctk.CTkEntry(f_form, width=280, validate="key", validatecommand=self.vcmd_num)
        self.e_tasa.grid(row=4, column=1, padx=10, pady=6)

        self.sw_manual = ctk.CTkSwitch(f_form, text="Forzar uso de Tasa Manual (Ignorar BCV)")
        self.sw_manual.grid(row=5, column=0, columnspan=2, pady=8)

        ctk.CTkLabel(f_form, text="Telegram Bot Token (Reportes):").grid(row=6, column=0, padx=10, pady=6, sticky="e")
        self.e_tg_token = ctk.CTkEntry(f_form, width=280, placeholder_text="Opcional: Token de @BotFather")
        self.e_tg_token.grid(row=6, column=1, padx=10, pady=6)

        ctk.CTkLabel(f_form, text="Telegram Chat ID (Dueño):").grid(row=7, column=0, padx=10, pady=6, sticky="e")
        self.e_tg_chat = ctk.CTkEntry(f_form, width=280, placeholder_text="Opcional: ID numérico de Telegram")
        self.e_tg_chat.grid(row=7, column=1, padx=10, pady=6)

        ctk.CTkButton(
            f_card, text="💾 GUARDAR Y APLICAR CONFIGURACIÓN",
            fg_color="#2ecc71", hover_color="#27ae60", height=42, font=("Roboto", 14, "bold"),
            command=self.guardar
        ).pack(pady=15)

        f_creditos = ctk.CTkFrame(f_card, corner_radius=8)
        f_creditos.pack(fill="x", padx=30, pady=(5, 15))
        ctk.CTkLabel(
            f_creditos,
            text="✨ Desarrollado por Varons Media\n"
                 "Desarrollo de Software, Producción Audiovisual & Publicidad Comercial\n"
                 "Soporte y Contacto Corporativo: contacto@varonsmedia.com",
            font=("Roboto", 11, "bold"),
            text_color="#3498db",
            justify="center"
        ).pack(pady=10)

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
            mostrar_fiscal
        )
        self.app_parent.hilo_tasa()
        messagebox.showinfo("Configuración Guardada", "Los parámetros y la visibilidad fiscal han sido actualizados.")