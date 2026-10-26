import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
import database
from controlador_configuracion import ConfigController

class ReportesController:
    @staticmethod
    def enviar_telegram(mensaje):
        conf = ConfigController.obtener_config()
        token = conf[5] if len(conf) > 5 else ""
        chat_id = conf[6] if len(conf) > 6 else ""
        if not token or not chat_id:
            return False, "Telegram no configurado en el módulo Empresa."
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            datos = urllib.parse.urlencode({'chat_id': chat_id, 'text': mensaje, 'parse_mode': 'Markdown'}).encode('utf-8')
            req = urllib.request.Request(url, data=datos)
            with urllib.request.urlopen(req, timeout=8) as resp:
                return (resp.status == 200), "Enviado a Telegram exitosamente."
        except Exception as e:
            return False, f"No se pudo enviar a Telegram: {e}"

    @staticmethod
    def obtener_resumen_periodos():
        conn = database.conectar_db()
        c = conn.cursor()

        hoy_str = datetime.now().strftime("%Y-%m-%d")
        ayer_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        mes_str = datetime.now().strftime("%Y-%m")

        c.execute("""SELECT COUNT(*), IFNULL(SUM(total_usd), 0), IFNULL(SUM(total_bs), 0)
                     FROM Ventas WHERE IFNULL(caja_sesion_id, 0) = 0 AND estado='COMPLETADA'""")
        turno_cant, turno_usd, turno_bs = c.fetchone()

        c.execute("""SELECT IFNULL(SUM((dv.precio_unitario_usd - dv.costo_unitario_usd) * dv.cantidad), 0)
                     FROM Detalle_Ventas dv
                     JOIN Ventas v ON dv.venta_id = v.id
                     WHERE IFNULL(v.caja_sesion_id, 0) = 0 AND v.estado='COMPLETADA'""")
        turno_ganancia = c.fetchone()[0]

        c.execute("""SELECT COUNT(*), IFNULL(SUM(total_usd), 0), IFNULL(SUM(total_bs), 0)
                     FROM Ventas WHERE substr(fecha, 1, 10) = ? AND estado='COMPLETADA'""", (hoy_str,))
        hoy_cant, hoy_usd, hoy_bs = c.fetchone()

        c.execute("""SELECT COUNT(*), IFNULL(SUM(total_usd), 0), IFNULL(SUM(total_bs), 0)
                     FROM Ventas WHERE substr(fecha, 1, 10) = ? AND estado='COMPLETADA'""", (ayer_str,))
        ayer_cant, ayer_usd, ayer_bs = c.fetchone()

        c.execute("""SELECT COUNT(*), IFNULL(SUM(total_usd), 0), IFNULL(SUM(total_bs), 0)
                     FROM Ventas WHERE substr(fecha, 1, 7) = ? AND estado='COMPLETADA'""", (mes_str,))
        mes_cant, mes_usd, mes_bs = c.fetchone()

        conn.close()
        return {
            'turno': {'cant': turno_cant, 'usd': turno_usd, 'bs': turno_bs, 'ganancia': turno_ganancia},
            'hoy': {'cant': hoy_cant, 'usd': hoy_usd, 'bs': hoy_bs},
            'ayer': {'cant': ayer_cant, 'usd': ayer_usd, 'bs': ayer_bs},
            'mes': {'cant': mes_cant, 'usd': mes_usd, 'bs': mes_bs}
        }

    @staticmethod
    def ejecutar_corte_z(tasa_actual, es_automatico=False):
        conn = database.conectar_db()
        c = conn.cursor()

        c.execute("""SELECT id, total_usd, total_bs, metodo_pago 
                     FROM Ventas WHERE IFNULL(caja_sesion_id, 0) = 0 AND estado='COMPLETADA'""")
        ventas_abiertas = c.fetchall()

        if not ventas_abiertas:
            conn.close()
            return False, "No hay ventas pendientes por cerrar en el turno actual (Caja en $0.00)."

        cant_ventas = len(ventas_abiertas)
        total_usd = sum(v[1] for v in ventas_abiertas)
        total_bs = sum(v[2] for v in ventas_abiertas)

        c.execute("""SELECT IFNULL(SUM((dv.precio_unitario_usd - dv.costo_unitario_usd) * dv.cantidad), 0)
                     FROM Detalle_Ventas dv
                     JOIN Ventas v ON dv.venta_id = v.id
                     WHERE IFNULL(v.caja_sesion_id, 0) = 0 AND v.estado='COMPLETADA'""")
        ganancia_usd = c.fetchone()[0]

        efec_usd = 0.0
        punto_bs = 0.0
        pm_bs = 0.0

        for _, v_usd, v_bs, mp in ventas_abiertas:
            mp_str = str(mp or "")
            if "Efec $" in mp_str:
                efec_usd += v_usd
            elif "Punto Bs" in mp_str:
                punto_bs += v_bs
            elif "PM Bs" in mp_str:
                pm_bs += v_bs

        desglose_resumen = f"Efec $: ${efec_usd:.2f} | Punto: Bs.{punto_bs:.2f} | PagoMóvil: Bs.{pm_bs:.2f}"
        ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute("""INSERT INTO Cortes_Z (fecha_corte, total_ventas, total_usd, total_bs, ganancia_usd, tasa_bcv, desglose_pagos)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (ahora_str, cant_ventas, round(total_usd, 2), round(total_bs, 2), round(ganancia_usd, 2), tasa_actual, desglose_resumen))
        corte_id = c.lastrowid

        c.execute("UPDATE Ventas SET caja_sesion_id = ? WHERE IFNULL(caja_sesion_id, 0) = 0", (corte_id,))
        conn.commit()
        conn.close()

        hoy_fecha = datetime.now().strftime("%Y-%m-%d")
        try:
            with open("ultimo_corte.txt", "w", encoding="utf-8") as f:
                f.write(hoy_fecha)
        except Exception:
            pass

        conf = ConfigController.obtener_config()
        os.makedirs("Reportes", exist_ok=True)
        tipo_titulo = "CORTE Z AUTOMÁTICO" if es_automatico else "CORTE Z DE CAJA"
        mensaje_tg = (
            f"📊 *{tipo_titulo} #{corte_id:04d}*\n"
            f"🏢 *{conf[0]}*\n"
            f"📅 Fecha: `{ahora_str}`\n"
            f"────────────────────\n"
            f"🛒 Ventas Cerradas: *{cant_ventas}*\n"
            f"💵 Total Vendido ($): *${total_usd:.2f}*\n"
            f"🇻🇪 Total Vendido (Bs): *Bs. {total_bs:.2f}*\n"
            f"📈 Ganancia Estimada: *+${ganancia_usd:.2f}*\n"
            f"────────────────────\n"
            f"💳 *Desglose por Método:*\n"
            f"• Efectivo $: `${efec_usd:.2f}`\n"
            f"• Punto de Venta: `Bs. {punto_bs:.2f}`\n"
            f"• Pago Móvil: `Bs. {pm_bs:.2f}`\n"
            f"────────────────────\n"
            f"✅ _Turno reiniciado a $0.00 — Varons Media POS_"
        )

        ruta_rep = os.path.join("Reportes", f"Corte_Z_{corte_id:04d}.txt")
        try:
            with open(ruta_rep, "w", encoding="utf-8") as f:
                f.write(mensaje_tg.replace("*", "").replace("`", "").replace("_", ""))
        except Exception:
            pass

        _, info_tg = ReportesController.enviar_telegram(mensaje_tg)
        estado_msg = f"Corte Z #{corte_id:04d} realizado con éxito.\nEl turno actual se ha reiniciado a $0.00.\n\nTelegram: {info_tg}"
        return True, estado_msg

    @staticmethod
    def verificar_corte_z_retroactivo(tasa_actual):
        hoy_str = datetime.now().strftime("%Y-%m-%d")
        ultimo = ""
        if os.path.exists("ultimo_corte.txt"):
            try:
                with open("ultimo_corte.txt", "r", encoding="utf-8") as f:
                    ultimo = f.read().strip()
            except Exception:
                pass

        if ultimo != hoy_str:
            conn = database.conectar_db()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM Ventas WHERE IFNULL(caja_sesion_id, 0) = 0 AND substr(fecha, 1, 10) < ?", (hoy_str,))
            pendientes_ayer = c.fetchone()[0]
            conn.close()
            if pendientes_ayer > 0:
                ReportesController.ejecutar_corte_z(tasa_actual, es_automatico=True)