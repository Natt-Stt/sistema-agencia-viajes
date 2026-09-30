"""Acceso a datos de la tabla `destinos`.

Esta clase es la ÚNICA que conoce SQL para destinos. El resto del sistema pide
"guarda este destino" o "dame los disponibles" sin saber cómo se almacenan.

Seguridad (RNF06): todas las consultas usan parámetros `?`. Los valores del
usuario NUNCA se pegan dentro del texto SQL (nada de f-strings ni concatenación),
así una entrada como  '; DROP TABLE destinos; --  se guarda como texto inofensivo.
"""
import sqlite3

from ..errores import ErrorNegocio
from ..models.destino import Destino


class RepositorioDestinos:
    def __init__(self, conexion: sqlite3.Connection):
        self._con = conexion

    def guardar(self, destino: Destino) -> Destino:
        """Inserta si es nuevo (id None) o actualiza si ya existe."""
        try:
            # `with conexion` = transacción: confirma (commit) si todo sale bien
            # y deshace (rollback) si ocurre un error.
            with self._con:
                if destino.id is None:
                    cursor = self._con.execute(
                        "INSERT INTO destinos "
                        "(nombre, zona, descripcion, duracion_dias, costo_base, disponible) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (destino.nombre, destino.zona, destino.descripcion,
                         destino.duracion_dias, destino.costo_base,
                         int(destino.disponible)),
                    )
                    destino.asignar_id(cursor.lastrowid)
                else:
                    cursor = self._con.execute(
                        "UPDATE destinos SET nombre = ?, zona = ?, descripcion = ?, "
                        "duracion_dias = ?, costo_base = ?, disponible = ? WHERE id = ?",
                        (destino.nombre, destino.zona, destino.descripcion,
                         destino.duracion_dias, destino.costo_base,
                         int(destino.disponible), destino.id),
                    )
                    if cursor.rowcount == 0:
                        raise ErrorNegocio("El destino indicado no existe.")
        except sqlite3.IntegrityError as error:
            # Se traduce el error técnico a un mensaje seguro (sin detalles internos).
            if "UNIQUE" in str(error):
                raise ErrorNegocio("Ya existe un destino con ese nombre.") from None
            raise ErrorNegocio("Los datos no cumplen las restricciones del sistema.") from None
        return destino

    def buscar(self, id_destino: int) -> Destino | None:
        fila = self._con.execute(
            "SELECT * FROM destinos WHERE id = ?", (id_destino,)
        ).fetchone()
        return self._a_destino(fila) if fila else None

    def buscar_por_nombre(self, nombre: str) -> Destino | None:
        fila = self._con.execute(
            "SELECT * FROM destinos WHERE nombre = ?", (nombre,)
        ).fetchone()
        return self._a_destino(fila) if fila else None

    def listar(self, solo_disponibles: bool = False) -> list[Destino]:
        if solo_disponibles:
            filas = self._con.execute(
                "SELECT * FROM destinos WHERE disponible = 1 ORDER BY nombre"
            ).fetchall()
        else:
            filas = self._con.execute(
                "SELECT * FROM destinos ORDER BY nombre"
            ).fetchall()
        return [self._a_destino(fila) for fila in filas]

    def eliminar(self, id_destino: int) -> None:
        try:
            with self._con:
                cursor = self._con.execute(
                    "DELETE FROM destinos WHERE id = ?", (id_destino,)
                )
        except sqlite3.IntegrityError:
            # ON DELETE RESTRICT: la base de datos se niega si está en un paquete (R8).
            raise ErrorNegocio(
                "No se puede eliminar: el destino forma parte de un paquete."
            ) from None
        if cursor.rowcount == 0:
            raise ErrorNegocio("El destino indicado no existe.")

    def esta_en_paquete(self, id_destino: int) -> bool:
        fila = self._con.execute(
            "SELECT 1 FROM paquete_destino WHERE id_destino = ? LIMIT 1",
            (id_destino,),
        ).fetchone()
        return fila is not None

    @staticmethod
    def _a_destino(fila: sqlite3.Row) -> Destino:
        return Destino(
            nombre=fila["nombre"],
            zona=fila["zona"],
            duracion_dias=fila["duracion_dias"],
            costo_base=fila["costo_base"],
            descripcion=fila["descripcion"],
            disponible=bool(fila["disponible"]),
            id_destino=fila["id"],
        )
