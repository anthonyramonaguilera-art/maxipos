import os
import sys
import json
import urllib.request
import subprocess
import threading
from tkinter import messagebox

VERSION_ACTUAL = "2.0"
URL_VERSION_JSON = "https://raw.githubusercontent.com/anthonyramonaguilera-art/maxipos/main/version.json"

def verificar_actualizacion_fondo(parent=None):
    threading.Thread(target=_ejecutar_revision, args=(parent,), daemon=True).start()

def _ejecutar_revision(parent):
    try:
        req = urllib.request.Request(URL_VERSION_JSON, headers={'User-Agent': 'VaronsMedia-POS-Updater'})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        version_remota = str(data.get("version", "2.0")).strip()
        url_descarga = data.get("download_url", "").strip()
        cambios = data.get("cambios", "Mejoras de estabilidad y nuevas funciones.")

        if float(version_remota) > float(VERSION_ACTUAL) and url_descarga:
            if parent:
                parent.after(0, lambda: _notificar_actualizacion(version_remota, url_descarga, cambios))
    except Exception:
        pass

def _notificar_actualizacion(version_remota, url_descarga, cambios):
    msg = (f"🚀 Nueva actualización disponible de Varons Media (v{version_remota})\n\n"
           f"Novedades:\n{cambios}\n\n"
           f"¿Desea actualizar el sistema automáticamente ahora?")
    if messagebox.askyesno("Actualización Disponible | Varons Media", msg):
        threading.Thread(target=_descargar_e_instalar, args=(url_descarga,), daemon=True).start()

def _descargar_e_instalar(url_descarga):
    try:
        temp_dir = os.environ.get("TEMP", "C:\\Temp")
        instalador_path = os.path.join(temp_dir, "MaxiPOS_Update_VaronsMedia.exe")

        urllib.request.urlretrieve(url_descarga, instalador_path)

        cmd = f'"{instalador_path}" /SILENT /SUPPRESSMSGBOXES /NORESTART'
        subprocess.Popen(cmd, shell=True)
        os._exit(0)
    except Exception as e:
        messagebox.showerror("Error de Actualización", f"No se pudo completar la descarga:\n{e}")