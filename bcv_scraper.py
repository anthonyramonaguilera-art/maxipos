import urllib.request
import ssl
import json
import re

def obtener_tasa_bcv():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    # Fuente 1: DolarApi Venezuela (Oficial BCV en JSON de alta velocidad)
    try:
        req = urllib.request.Request("https://ve.dolarapi.com/v1/dolares/oficial", headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            promedio = data.get("promedio")
            if promedio and float(promedio) > 1.0:
                return round(float(promedio), 4)
    except Exception:
        pass

    # Fuente 2: PyDolarVE API Oficial BCV
    try:
        req = urllib.request.Request("https://pydolarve.org/api/v1/dollar?page=bcv", headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            usd = data.get("monitors", {}).get("usd", {}).get("price")
            if usd and float(usd) > 1.0:
                return round(float(usd), 4)
    except Exception:
        pass

    # Fuente 3: Scraping directo del portal oficial del BCV
    try:
        req = urllib.request.Request("https://www.bcv.org.ve/", headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        match = re.search(r'id="dolar".*?<strong>\s*([\d,]+)\s*</strong>', html, re.DOTALL)
        if match:
            valor_str = match.group(1).replace(',', '.')
            val = round(float(valor_str), 4)
            if val > 1.0:
                return val
    except Exception:
        pass

    return None