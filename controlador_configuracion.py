import database

class ConfigController:
    @staticmethod
    def obtener_config():
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("""SELECT empresa_nombre, empresa_rif, empresa_direccion, tasa_manual, usar_tasa_manual, 
                            IFNULL(telegram_token, ''), IFNULL(telegram_chat_id, ''), IFNULL(mostrar_datos_fiscales, 1) 
                     FROM Configuracion WHERE id=1""")
        res = c.fetchone()
        conn.close()
        if not res:
            return ("MAXI POS", "J-0000000-0", "Ciudad Guayana, Bolívar", 1.0, 0, "", "", 1)
        return res

    @staticmethod
    def guardar_config(nombre, rif, direccion, tasa, usar, tg_token="", tg_chat="", mostrar_datos=1):
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("""UPDATE Configuracion 
                     SET empresa_nombre=?, empresa_rif=?, empresa_direccion=?, tasa_manual=?, usar_tasa_manual=?, 
                         telegram_token=?, telegram_chat_id=?, mostrar_datos_fiscales=? 
                     WHERE id=1""",
                  (nombre.upper().strip(), rif.upper().strip(), direccion.upper().strip(), float(tasa), int(usar), 
                   tg_token.strip(), tg_chat.strip(), int(mostrar_datos)))
        conn.commit()
        conn.close()
        return True