"""Acceso a datos de la tabla `usuarios`.

RUT y teléfono se CIFRAN antes de guardarse y se DESCIFRAN al leerse. En la base de
datos nunca quedan en texto plano: si alguien copia el archivo .db, solo ve basura
ilegible sin la clave (que vive fuera de la base de datos).
"""
import sqlite3

from ..errores import ErrorNegocio
from ..models.administrador import Administrador
from ..models.cliente import Cliente
from ..models.usuario import Usuario
from ..seguridad import CifradorDatos


class RepositorioUsuarios:
    def __init__(self, conexion: sqlite3.Connection, cifrador: CifradorDatos):
        self._con = conexion
        self._cifrador = cifrador

    def guardar(self, usuario: Usuario) -> Usuario:
        if usuario.id is not None:
            raise ErrorNegocio("El usuario ya existe.")
        rut = telefono = None
        if isinstance(usuario, Cliente):
            rut = self._cifrador.cifrar(usuario.rut)
            telefono = self._cifrador.cifrar(usuario.telefono)
        try:
            with self._con:
                cursor = self._con.execute(
                    "INSERT INTO usuarios (nombre, correo, password_hash, rol, rut, telefono) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (usuario.nombre, usuario.correo, usuario.password_hash,
                     usuario.rol, rut, telefono),
                )
        except sqlite3.IntegrityError as error:
            if "UNIQUE" in str(error):
                raise ErrorNegocio("Ya existe una cuenta registrada con ese correo.") from None
            raise ErrorNegocio("Los datos no cumplen las restricciones del sistema.") from None
        usuario.asignar_id(cursor.lastrowid)
        return usuario

    def buscar_por_correo(self, correo: str) -> Usuario | None:
        fila = self._con.execute(
            "SELECT * FROM usuarios WHERE correo = ?", (correo,)
        ).fetchone()
        return self._a_usuario(fila) if fila else None

    def buscar(self, id_usuario: int) -> Usuario | None:
        fila = self._con.execute(
            "SELECT * FROM usuarios WHERE id = ?", (id_usuario,)
        ).fetchone()
        return self._a_usuario(fila) if fila else None

    def _a_usuario(self, fila: sqlite3.Row) -> Usuario:
        if fila["rol"] == "CLIENTE":
            return Cliente(
                nombre=fila["nombre"],
                rut=self._cifrador.descifrar(fila["rut"]),
                correo=fila["correo"],
                telefono=self._cifrador.descifrar(fila["telefono"]),
                password_hash=fila["password_hash"],
                id_usuario=fila["id"],
            )
        return Administrador(
            nombre=fila["nombre"], correo=fila["correo"],
            password_hash=fila["password_hash"], id_usuario=fila["id"],
        )
