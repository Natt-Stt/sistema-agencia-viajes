"""Persistencia de paquetes y su relación muchos-a-muchos con destinos."""
import sqlite3

from ..errores import ErrorNegocio
from ..models.destino import Destino
from ..models.paquete import EstadoPaquete, Paquete


class RepositorioPaquetes:
    def __init__(self, conexion: sqlite3.Connection):
        self._con = conexion

    def guardar(self, paquete: Paquete) -> Paquete:
        try:
            with self._con:
                if paquete.id is None:
                    cursor = self._con.execute(
                        "INSERT INTO paquetes (nombre, fecha_salida, fecha_regreso, cupo_maximo, "
                        "temporada, margen, precio_por_persona, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (paquete.nombre, paquete.fecha_salida, paquete.fecha_regreso,
                         paquete.cupo_maximo, paquete.temporada, paquete.margen,
                         paquete.precio_por_persona, paquete.estado.value),
                    )
                    paquete.asignar_id(cursor.lastrowid)
                else:
                    self._con.execute(
                        "UPDATE paquetes SET nombre = ?, fecha_salida = ?, fecha_regreso = ?, "
                        "cupo_maximo = ?, temporada = ?, margen = ?, precio_por_persona = ?, estado = ? "
                        "WHERE id = ?",
                        (paquete.nombre, paquete.fecha_salida, paquete.fecha_regreso,
                         paquete.cupo_maximo, paquete.temporada, paquete.margen,
                         paquete.precio_por_persona, paquete.estado.value, paquete.id),
                    )
                    self._con.execute("DELETE FROM paquete_destino WHERE id_paquete = ?", (paquete.id,))
                self._con.executemany(
                    "INSERT INTO paquete_destino (id_paquete, id_destino) VALUES (?, ?)",
                    [(paquete.id, destino.id) for destino in paquete.destinos],
                )
        except sqlite3.IntegrityError:
            raise ErrorNegocio("No se pudo guardar el paquete con los datos indicados.") from None
        return paquete

    def buscar(self, id_paquete: int) -> Paquete | None:
        fila = self._con.execute("SELECT * FROM paquetes WHERE id = ?", (id_paquete,)).fetchone()
        return self._a_paquete(fila) if fila else None

    def listar(self, solo_publicados=False) -> list[Paquete]:
        consulta = "SELECT * FROM paquetes"
        if solo_publicados:
            consulta += " WHERE estado = 'PUBLICADO'"
        consulta += " ORDER BY fecha_salida, nombre"
        return [self._a_paquete(fila) for fila in self._con.execute(consulta).fetchall()]

    def reservas_activas(self, id_paquete: int) -> int:
        fila = self._con.execute(
            "SELECT COALESCE(SUM(cantidad_personas), 0) AS total FROM reservas "
            "WHERE id_paquete = ? AND estado IN ('PENDIENTE', 'CONFIRMADA')", (id_paquete,)
        ).fetchone()
        return fila["total"]

    def _a_paquete(self, fila):
        filas_destinos = self._con.execute(
            "SELECT d.* FROM destinos d JOIN paquete_destino pd ON pd.id_destino = d.id "
            "WHERE pd.id_paquete = ? ORDER BY d.nombre", (fila["id"],)
        ).fetchall()
        destinos = [Destino(d["nombre"], d["zona"], d["duracion_dias"], d["costo_base"],
                            d["descripcion"], bool(d["disponible"]), d["id"])
                    for d in filas_destinos]
        return Paquete(
            fila["nombre"], fila["fecha_salida"], fila["fecha_regreso"], fila["cupo_maximo"],
            destinos, fila["margen"], fila["temporada"], fila["precio_por_persona"],
            EstadoPaquete(fila["estado"]), fila["id"],
        )