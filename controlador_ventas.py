import os
from datetime import datetime
import database
from controlador_configuracion import ConfigController

class VentasController:
    @staticmethod
    def procesar_venta(carrito, total_usd, total_bs, tasa, metodo_pago, cliente_id=1, usuario_id=1):
        conn = database.conectar_db()
        c = conn.cursor()
        ahora_sql = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ahora_ticket = datetime.now().strftime("%d/%m/%Y %H:%M")

        try:
            c.execute("""INSERT INTO Ventas (fecha, cliente_id, usuario_id, caja_sesion_id, total_usd, total_bs, tasa_aplicada, metodo_pago, estado)
                         VALUES (?, ?, ?, 0, ?, ?, ?, ?, 'COMPLETADA')""",
                      (ahora_sql, cliente_id, usuario_id, round(total_usd, 2), round(total_bs, 2), tasa, metodo_pago))
            venta_id = c.lastrowid

            for item in carrito:
                c.execute("""INSERT INTO Detalle_Ventas (venta_id, producto_id, cantidad, precio_unitario_usd, costo_unitario_usd, subtotal_usd)
                             VALUES (?, ?, ?, ?, ?, ?)""",
                          (venta_id, item['id'], item['cantidad'], item['precio_usd'], item['costo_usd'], item['subtotal_usd']))

                c.execute("UPDATE Productos SET stock_actual = stock_actual - ? WHERE id = ?", (item['cantidad'], item['id']))

                c.execute("""INSERT INTO Movimientos_Stock (producto_id, tipo_movimiento, cantidad, fecha, referencia)
                             VALUES (?, '- VENTA', ?, ?, ?)""",
                          (item['id'], item['cantidad'], ahora_sql, f"Venta Factura #{venta_id}"))

            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            raise e

        conn.close()
        ruta_ticket = VentasController.generar_ticket_txt(venta_id, ahora_ticket, carrito, total_usd, total_bs, tasa, metodo_pago)
        return venta_id, ruta_ticket

    @staticmethod
    def generar_ticket_txt(venta_id, fecha_str, carrito, total_usd, total_bs, tasa, metodo_pago):
        conf = ConfigController.obtener_config()
        mostrar_fiscal = conf[7] if len(conf) > 7 else 1

        os.makedirs("Tickets", exist_ok=True)
        ruta = os.path.join("Tickets", f"Ticket_{venta_id}.txt")

        if mostrar_fiscal == 1:
            cabecera = [
                "================================",
                conf[0][:30].center(32),
                f"RIF: {conf[1]}".center(32),
                f"{conf[2][:30]}".center(32),
                "================================"
            ]
        else:
            cabecera = [
                "================================",
                "       NOTA DE ENTREGA POS      ",
                "================================"
            ]

        lineas = cabecera + [
            f"FECHA: {fecha_str}",
            f"TICKET NRO: {venta_id:06d}",
            f"TASA BCV: {tasa} Bs/$",
            "--------------------------------",
            "CANT DESCRIPCION        SUBTOTAL",
            "--------------------------------"
        ]

        for it in carrito:
            cant_str = f"{it['cantidad']:4.1f}"
            nom_str = it['nombre'][:16].ljust(16)
            sub_str = f"${it['subtotal_usd']:.2f}".rjust(7)
            lineas.append(f"{cant_str} {nom_str}   {sub_str}")
            if it['cantidad'] > 1:
                lineas.append(f"     (Und: ${it['precio_usd']:.2f})")

        lineas.extend([
            "--------------------------------",
            f"TOTAL $: {total_usd:.2f}".rjust(32),
            f"TOTAL BS: {total_bs:.2f}".rjust(32),
            "--------------------------------",
            "PAGO:                           ",
            f"  {metodo_pago}",
            "================================",
            "       GRACIAS POR SU COMPRA!   ",
            "     Powered by Varons Media    ",
            "================================",
            "\n"
        ])

        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))
        return ruta