from datetime import datetime
import database
from controlador_reportes import ReportesController

class ProveedoresController:
    @staticmethod
    def enviar_alertas_telegram():
        conn = database.conectar_db()
        c = conn.cursor()
        hoy = datetime.now().strftime("%Y-%m-%d")
        c.execute("""SELECT cp.id, p.nombre, cp.descripcion, (cp.monto_total_usd - cp.abonado_usd), cp.fecha_vencimiento
                     FROM Cuentas_Pagar cp
                     LEFT JOIN Proveedores p ON cp.proveedor_id = p.id
                     WHERE cp.estado = 'PENDIENTE' AND cp.fecha_vencimiento <= ?""", (hoy,))
        vencidas = c.fetchall()
        conn.close()

        if vencidas:
            lineas = ["⚠️ *ALERTA DE CUENTAS POR PAGAR (MAXI POS)*\n"]
            for v in vencidas:
                lineas.append(f"• *{v[1] or 'Proveedor'}*: {v[2]} — Restante: *${v[3]:.2f}* (Vence: {v[4]})")
            ReportesController.enviar_telegram("\n".join(lineas))