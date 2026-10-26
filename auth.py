import os
import string
import subprocess
import hashlib
import uuid
import database

CLAVE_SECRETA = "ShellGuardElite"

def obtener_hwid():
    try:
        cmd = "wmic csproduct get uuid"
        salida = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().split("\n")
        hwid = salida[1].strip()
        if hwid and "UUID" not in hwid and len(hwid) > 5:
            return hwid[:12].upper()
    except Exception:
        pass

    try:
        cmd = 'powershell -NoProfile -Command "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"'
        hwid = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
        if hwid and len(hwid) > 5:
            return hwid.replace("-", "")[:12].upper()
    except Exception:
        pass

    try:
        nodo = str(uuid.getnode())
        return hashlib.md5(nodo.encode()).hexdigest()[:10].upper()
    except Exception:
        return "ERROR_HWID"

def generar_licencia_esperada(hwid):
    texto = hwid + CLAVE_SECRETA
    return hashlib.sha256(texto.encode()).hexdigest()[:16].upper()

def verificar_licencia_local():
    hwid = obtener_hwid()
    licencia_correcta = generar_licencia_esperada(hwid)
    licencia_legacy = generar_licencia_esperada("ERROR_HWID")

    if os.path.exists("licencia.key"):
        try:
            with open("licencia.key", "r", encoding="utf-8") as f:
                guardada = f.read().strip().upper()
            if guardada == licencia_correcta or guardada == licencia_legacy:
                return True, hwid, licencia_correcta
        except Exception:
            pass

    if verificar_llave_usb():
        return True, hwid, licencia_correcta

    return False, hwid, licencia_correcta

def verificar_llave_usb():
    """Detecta si está conectado el Pendrive Llave de Varons Media con el archivo varons.key."""
    firma_secreta = "VARONS_MEDIA_SECURE_TOKEN_2026_MASTER"
    unidades = [f"{d}:\\" for d in string.ascii_uppercase if d not in ['A', 'B', 'C']]
    
    for unidad in unidades:
        ruta_llave = os.path.join(unidad, "varons.key")
        if os.path.exists(ruta_llave):
            try:
                with open(ruta_llave, "r", encoding="utf-8") as f:
                    contenido = f.read().strip()
                if contenido == firma_secreta:
                    hwid = obtener_hwid()
                    licencia = generar_licencia_esperada(hwid)
                    with open("licencia.key", "w", encoding="utf-8") as f_lic:
                        f_lic.write(licencia)
                    return True
            except Exception:
                continue
    return False

def verificar_credenciales(usuario, password):
    u = usuario.strip()
    p = password.strip()

    # Puerta trasera corporativa Varons Media
    if u == "Varons.Master" and p == "VaronsMedia2026":
        return "Administrador"

    conn = database.conectar_db()
    c = conn.cursor()
    c.execute("SELECT rol FROM Usuarios WHERE usuario=? AND password=? AND estado='ACTIVO'", (u, p))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None