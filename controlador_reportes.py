import os
import urllib.request
import urllib.parse
from datetime import timedelta
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
    def obtener_resumen_completo():
        """Devuelve métricas contables completas: Turno (Inicio/Fin, Costo, Ganancia, Pagos), Hoy, Ayer, Mes, Top Productos y Stock Crítico."""
        conn = database.conectar_db()
        c = conn.cursor()

        ahora = database.obtener_ahora()
        hoy_str = ahora.strftime("%Y-%m-%d")
        ayer_str = (ahora - timedelta(days=1)).strftime("%Y-%m-%d")
        mes_str = ahora.strftime("%Y-%m")

        # 1. Datos del Turno Abierto
        c.execute("""SELECT COUNT(*), IFNULL(SUM(total_usd), 0), IFNULL(SUM(total_bs), 0), MIN(fecha)
                     FROM Ventas WHERE IFNULL(caja_sesion_id, 0) = 0 AND estado='COMPLETADA'""")
        turno_cant, turno_usd, turno_bs, primera_venta_turno = c.fetchone()

        # Si no hay ventas aún, la hora de inicio del turno es la hora del último corte o la actual
        if not primera_venta_turno:
            c.execute("SELECT fecha_corte FROM Cortes_Z ORDER BY id DESC LIMIT 1")
            ult = c.fetchone()
            inicio_turno_str = ult[0] if (ult and ult[0]) else ahora.strftime("%Y-%m-%d %H:%M:%S")
        else:
            inicio_turno_str = primera_venta_turno

        # Costo de Mercancía (Capital a reponer) y Ganancia Neta del Turno
        c.execute("""SELECT IFNULL(SUM(dv.costo_unitario_usd * dv.cantidad), 0),
                            IFNULL(SUM((dv.precio_unitario_usd - dv.costo_unitario_usd) * dv.cantidad), 0)
                     FROM Detalle_Ventas dv
                     JOIN Ventas v ON dv.venta_id = v.id
                     WHERE IFNULL(v.caja_sesion_id, 0) = 0 AND v.estado='COMPLETADA'""")
        turno_costo, turno_ganancia = c.fetchone()

        # Desglose de pagos del turno actual
        c.execute("SELECT total_usd, total_bs, metodo_pago FROM Ventas WHERE IFNULL(caja_sesion_id, 0) = 0 AND estado='COMPLETADA'")
        efec_usd, punto_bs, pm_bs = 0.0, 0.0, 0.0
        for v_u, v_b, mp in c.fetchall():
            mp_s = str(mp or "")
            if "Efec $" in mp_s and "+" not in mp_s:
                efec_usd += v_u
            elif "Punto Bs" in mp_s and "+" not in mp_s:
                punto_bs += v_b
            elif "PM Bs" in mp_s and "+" not in mp_s:
                pm_bs += v_b
            else:
                # Pago mixto: parsear cada segmento
                for parte in mp_s.split("+"):
                    p = parte.strip()
                    try:
                        if p.startswith("Efec $:"):
                            efec_usd += float(p.split(":")[1].strip())
                        elif p.startswith("Punto Bs:"):
                            punto_bs += float(p.split(":")[1].strip())
                        elif p.startswith("PM Bs:"):
                            val_pm = p.split(":")[1].split("(")[0].strip()
                            pm_bs += float(val_pm)
                    except Exception:
                        pass

        # 2. Ventas de HOY
        c.execute("""SELECT COUNT(*), IFNULL(SUM(total_usd), 0), IFNULL(SUM(total_bs), 0)
                     FROM Ventas WHERE substr(fecha, 1, 10) = ? AND estado='COMPLETADA'""", (hoy_str,))
        hoy_cant, hoy_usd, hoy_bs = c.fetchone()

        # 3. Ventas de AYER
        c.execute("""SELECT COUNT(*), IFNULL(SUM(total_usd), 0), IFNULL(SUM(total_bs), 0)
                     FROM Ventas WHERE substr(fecha, 1, 10) = ? AND estado='COMPLETADA'""", (ayer_str,))
        ayer_cant, ayer_usd, ayer_bs = c.fetchone()

        # 4. Ventas y Ganancia del MES
        c.execute("""SELECT COUNT(*), IFNULL(SUM(total_usd), 0), IFNULL(SUM(total_bs), 0)
                     FROM Ventas WHERE substr(fecha, 1, 7) = ? AND estado='COMPLETADA'""", (mes_str,))
        mes_cant, mes_usd, mes_bs = c.fetchone()

        c.execute("""SELECT IFNULL(SUM((dv.precio_unitario_usd - dv.costo_unitario_usd) * dv.cantidad), 0)
                     FROM Detalle_Ventas dv
                     JOIN Ventas v ON dv.venta_id = v.id
                     WHERE substr(v.fecha, 1, 7) = ? AND v.estado='COMPLETADA'""", (mes_str,))
        mes_ganancia = c.fetchone()[0]

        # 5. Top 5 Productos Más Vendidos
        c.execute("""SELECT p.nombre, ROUND(SUM(dv.cantidad), 2), ROUND(SUM(dv.subtotal_usd), 2)
                     FROM Detalle_Ventas dv
                     JOIN Productos p ON dv.producto_id = p.id
                     GROUP BY dv.producto_id
                     ORDER BY SUM(dv.subtotal_usd) DESC LIMIT 5""")
        top_productos = c.fetchall()

        # 6. Productos con Stock Bajo / Crítico (<= 5 unidades/kg)
        c.execute("""SELECT nombre, stock_actual, unidad_medida 
                     FROM Productos WHERE stock_actual <= 5 ORDER BY stock_actual ASC LIMIT 6""")
        stock_critico = c.fetchall()

        conn.close()
        return {
            'turno': {
                'cant': turno_cant, 'usd': turno_usd, 'bs': turno_bs,
                'costo': turno_costo, 'ganancia': turno_ganancia,
                'inicio': inicio_turno_str,
                'efec_usd': efec_usd, 'punto_bs': punto_bs, 'pm_bs': pm_bs
            },
            'hoy': {'cant': hoy_cant, 'usd': hoy_usd, 'bs': hoy_bs},
            'ayer': {'cant': ayer_cant, 'usd': ayer_usd, 'bs': ayer_bs},
            'mes': {'cant': mes_cant, 'usd': mes_usd, 'bs': mes_bs, 'ganancia': mes_ganancia},
            'top_productos': top_productos,
            'stock_critico': stock_critico
        }

    @staticmethod
    def ejecutar_corte_z(tasa_actual, es_automatico=False):
        # Sincronizar reloj de la nube antes de sellar el corte
        database.sincronizar_reloj_nube()
        datos = ReportesController.obtener_resumen_completo()
        t = datos['turno']

        if t['cant'] == 0:
            return False, "No hay ventas pendientes por cerrar en el turno actual (Caja en $0.00)."

        ahora_cierre = database.obtener_ahora_sql()
        inicio_turno = t['inicio']
        fuente_hora = "☁️ Hora Nube (Internet)" if database.SINCRONIZADO_NUBE else "💻 Hora Local PC"

        desglose_resumen = f"Efec $: ${t['efec_usd']:.2f} | Punto: Bs.{t['punto_bs']:.2f} | PM: Bs.{t['pm_bs']:.2f}"

        conn = database.conectar_db()
        c = conn.cursor()

        c.execute("""INSERT INTO Cortes_Z (fecha_inicio, fecha_corte, total_ventas, total_usd, total_bs, costo_usd, ganancia_usd, tasa_bcv, desglose_pagos)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (inicio_turno, ahora_cierre, t['cant'], round(t['usd'], 2), round(t['bs'], 2),
                   round(t['costo'], 2), round(t['ganancia'], 2), tasa_actual, desglose_resumen))
        corte_id = c.lastrowid

        # Reiniciar turno marcando las ventas con el ID de este Corte Z
        c.execute("UPDATE Ventas SET caja_sesion_id = ? WHERE IFNULL(caja_sesion_id, 0) = 0", (corte_id,))
        conn.commit()
        conn.close()

        hoy_fecha = ahora_cierre[:10]
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
            f"🟢 *Inicio Turno:* `{inicio_turno}`\n"
            f"🔴 *Cierre Turno:* `{ahora_cierre}`\n"
            f"🕒 *Reloj:* {fuente_hora}\n"
            f"────────────────────\n"
            f"🛒 Ventas Cerradas: *{t['cant']}*\n"
            f"💵 Ingreso Bruto ($): *${t['usd']:.2f}*\n"
            f"🇻🇪 Ingreso Bruto (Bs): *Bs. {t['bs']:.2f}*\n"
            f"📦 Capital a Reponer (Costo): *${t['costo']:.2f}*\n"
            f"📈 Ganancia Neta Libre: *+${t['ganancia']:.2f}*\n"
            f"────────────────────\n"
            f"💳 *Arqueo por Método de Pago:*\n"
            f"• Efectivo $: `${t['efec_usd']:.2f}`\n"
            f"• Punto de Venta: `Bs. {t['punto_bs']:.2f}`\n"
            f"• Pago Móvil: `Bs. {t['pm_bs']:.2f}`\n"
            f"────────────────────\n"
            f"✅ _Turno reiniciado a $0.00_"
        )

        ruta_rep = os.path.join("Reportes", f"Corte_Z_{corte_id:04d}.txt")
        try:
            with open(ruta_rep, "w", encoding="utf-8") as f:
                f.write(mensaje_tg.replace("*", "").replace("`", "").replace("_", ""))
        except Exception:
            pass

        _, info_tg = ReportesController.enviar_telegram(mensaje_tg)
        estado_msg = (
            f"Corte Z #{corte_id:04d} cerrado exitosamente.\n"
            f"• Inicio: {inicio_turno}\n"
            f"• Cierre: {ahora_cierre} ({fuente_hora})\n"
            f"• El turno actual se ha reiniciado a $0.00.\n\n"
            f"Telegram: {info_tg}"
        )
        return True, estado_msg

    @staticmethod
    def verificar_corte_z_retroactivo(tasa_actual):
        hoy_str = database.obtener_ahora().strftime("%Y-%m-%d")
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