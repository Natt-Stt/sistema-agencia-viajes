"""Persistencia transaccional de reservas, consultas y cambios de estado."""
import sqlite3

from ..errores import ErrorNegocio
from ..models.reserva import EstadoReserva, Reserva


class RepositorioReservas:
    def __init__(self, conexion: sqlite3.Connection):
        self._con = conexion

    def reservar(self, reserva: Reserva, hoy: str) -> Reserva:
        try:
            self._con.execute("BEGIN IMMEDIATE")
            paquete = self._con.execute(
                "SELECT fecha_salida, cupo_maximo, precio_por_persona, estado "
                "FROM paquetes WHERE id = ?", (reserva.id_paquete,)
            ).fetchone()
            if paquete is None or paquete["estado"] != "PUBLICADO":
                raise ErrorNegocio("El paquete no está disponible para reservar.")
            if paquete["fecha_salida"] < hoy:
                raise ErrorNegocio("No se puede reservar un paquete con salida vencida.")
            ocupados = self._con.execute(
                "SELECT COALESCE(SUM(cantidad_personas), 0) FROM reservas "
                "WHERE id_paquete = ? AND estado IN ('PENDIENTE', 'CONFIRMADA')",
                (reserva.id_paquete,),
            ).fetchone()[0]
            if ocupados + reserva.cantidad_personas > paquete["cupo_maximo"]:
                raise ErrorNegocio("No hay cupo suficiente para esa cantidad de personas.")
            duplicada = self._con.execute(
                "SELECT 1 FROM reservas WHERE id_cliente = ? AND id_paquete = ? "
                "AND estado IN ('PENDIENTE', 'CONFIRMADA') LIMIT 1",
                (reserva.id_cliente, reserva.id_paquete),
            ).fetchone()
            if duplicada:
                raise ErrorNegocio("Ya existe una reserva activa para este paquete.")
            reserva.total = paquete["precio_por_persona"] * reserva.cantidad_personas
            cursor = self._con.execute(
                "INSERT INTO reservas (id_cliente, id_paquete, cantidad_personas, fecha_emision, total) "
                "VALUES (?, ?, ?, ?, ?)",
                (reserva.id_cliente, reserva.id_paquete, reserva.cantidad_personas,
                 reserva.fecha_emision, reserva.total),
            )
            reserva.id = cursor.lastrowid
            self._con.commit()
        except sqlite3.IntegrityError as error:
            self._con.rollback()
            if "uq_reserva_activa_cliente_paquete" in str(error):
                raise ErrorNegocio("Ya existe una reserva activa para este paquete.") from None
            raise ErrorNegocio("No se pudo registrar la reserva.") from None
        except Exception:
            self._con.rollback()
            raise
        return reserva

    def buscar(self, id_reserva: int) -> Reserva | None:
        fila = self._con.execute("SELECT * FROM reservas WHERE id = ?", (id_reserva,)).fetchone()
        return self._a_reserva(fila) if fila else None

    def listar_por_cliente(self, id_cliente: int) -> list[Reserva]:
        filas = self._con.execute(
            "SELECT r.*, p.nombre AS nombre_paquete FROM reservas r "
            "JOIN paquetes p ON p.id = r.id_paquete WHERE r.id_cliente = ? "
            "ORDER BY r.fecha_emision DESC, r.id DESC", (id_cliente,)
        ).fetchall()
        return [self._a_reserva(fila) for fila in filas]

    def listar_todas(self) -> list[Reserva]:
        filas = self._con.execute(
            "SELECT r.*, p.nombre AS nombre_paquete FROM reservas r "
            "JOIN paquetes p ON p.id = r.id_paquete ORDER BY r.fecha_emision DESC, r.id DESC"
        ).fetchall()
        return [self._a_reserva(fila) for fila in filas]

    def reservas_activas(self, id_paquete: int) -> int:
        fila = self._con.execute(
            "SELECT COALESCE(SUM(cantidad_personas), 0) AS total FROM reservas "
            "WHERE id_paquete = ? AND estado IN ('PENDIENTE', 'CONFIRMADA')",
            (id_paquete,),
        ).fetchone()
        return fila["total"]

    def actualizar(self, reserva: Reserva) -> Reserva:
        with self._con:
            cursor = self._con.execute(
                "UPDATE reservas SET estado = ?, id_confirmado_por = ? WHERE id = ?",
                (reserva.estado.value, reserva.id_confirmado_por, reserva.id),
            )
        if cursor.rowcount == 0:
            raise ErrorNegocio("La reserva indicada no existe.")
        return reserva

    @staticmethod
    def _a_reserva(fila):
        nombre_paquete = fila["nombre_paquete"] if "nombre_paquete" in fila.keys() else None
        return Reserva(
            fila["id_cliente"], fila["id_paquete"], fila["cantidad_personas"],
            fila["total"], fila["fecha_emision"], EstadoReserva(fila["estado"]),
            fila["id"], fila["id_confirmado_por"], nombre_paquete,
        )