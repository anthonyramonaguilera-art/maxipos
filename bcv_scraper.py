import urllib.request
import ssl
import re

def obtener_tasa_bcv():
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        url = "https://www.bcv.org.ve/"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        match = re.search(r'id="dolar".*?<strong>\s*([\d,]+)\s*</strong>', html, re.DOTALL)
        if match:
            valor_str = match.group(1).replace(',', '.')
            return round(float(valor_str), 4)
    except Exception:
        pass
    return None