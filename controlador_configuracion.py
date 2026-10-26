import database

class ConfigController:
    @staticmethod
    def obtener_config():
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("""SELECT empresa_nombre, empresa_rif, empresa_direccion, tasa_manual, usar_tasa_manual, 
                            IFNULL(telegram_token, ''), IFNULL(telegram_chat_id, ''), 
                            IFNULL(mostrar_datos_fiscales, 1), IFNULL(puerto_balanza, 'COM3')
                     FROM Configuracion WHERE id=1""")
        res = c.fetchone()
        conn.close()
        if not res:
            return ("MAXI POS", "J-0000000-0", "Ciudad Guayana, Bolívar", 1.0, 0, "", "", 1, "COM3")
        return res

    @staticmethod
    def actualizar_cache_tasa(nueva_tasa):
        """Guarda la última tasa BCV descargada como respaldo automático en la base de datos."""
        try:
            conn = database.conectar_db()
            c = conn.cursor()
            c.execute("UPDATE Configuracion SET tasa_manual=? WHERE id=1 AND usar_tasa_manual=0", (float(nueva_tasa),))
            conn.commit()
            conn.close()
        except Exception:
            pass

    @staticmethod
    def guardar_config(nombre, rif, direccion, tasa, usar, tg_token="", tg_chat="", mostrar_datos=1, puerto_com="COM3"):
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("""UPDATE Configuracion 
                     SET empresa_nombre=?, empresa_rif=?, empresa_direccion=?, tasa_manual=?, usar_tasa_manual=?, 
                         telegram_token=?, telegram_chat_id=?, mostrar_datos_fiscales=?, puerto_balanza=? 
                     WHERE id=1""",
                  (nombre.upper().strip(), rif.upper().strip(), direccion.upper().strip(), float(tasa), int(usar), 
                   tg_token.strip(), tg_chat.strip(), int(mostrar_datos), puerto_com.upper().strip()))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def listar_usuarios():
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("SELECT id, usuario, rol, estado FROM Usuarios ORDER BY id ASC")
        rows = c.fetchall()
        conn.close()
        return rows

    @staticmethod
    def guardar_usuario(usuario, password, rol):
        u = usuario.strip()
        p = password.strip()
        if not u or not p:
            return False, "Usuario y contraseña requeridos."
        conn = database.conectar_db()
        c = conn.cursor()
        try:
            c.execute("SELECT id FROM Usuarios WHERE LOWER(usuario)=LOWER(?)", (u,))
            existente = c.fetchone()
            if existente:
                c.execute("UPDATE Usuarios SET password=?, rol=?, estado='ACTIVO' WHERE id=?", (p, rol, existente[0]))
                msg = f"Usuario '{u}' actualizado exitosamente."
            else:
                c.execute("INSERT INTO Usuarios (usuario, password, rol, estado) VALUES (?, ?, ?, 'ACTIVO')", (u, p, rol))
                msg = f"Usuario '{u}' creado exitosamente."
            conn.commit()
            return True, msg
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def eliminar_usuario(user_id):
        conn = database.conectar_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM Usuarios WHERE rol='Administrador' AND estado='ACTIVO'")
        total_admins = c.fetchone()[0]
        c.execute("SELECT rol FROM Usuarios WHERE id=?", (user_id,))
        r = c.fetchone()
        if r and r[0] == 'Administrador' and total_admins <= 1:
            conn.close()
            return False, "No puede eliminar al único Administrador activo del sistema."
        c.execute("DELETE FROM Usuarios WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        return True, "Usuario eliminado correctamente."