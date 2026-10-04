"""Entidad Reserva y transiciones de estado permitidas."""
from datetime import date
from enum import Enum

from ..errores import ErrorNegocio, ErrorValidacion


class EstadoReserva(str, Enum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"


class Reserva:
    def __init__(self, id_cliente, id_paquete, cantidad_personas, total,
                 fecha_emision=None, estado=EstadoReserva.PENDIENTE,
                 id_reserva=None, id_confirmado_por=None, nombre_paquete=None):
        if isinstance(cantidad_personas, bool) or not isinstance(cantidad_personas, int) or cantidad_personas < 1:
            raise ErrorValidacion("La cantidad de personas debe ser un entero mayor que cero.")
        if isinstance(total, bool) or not isinstance(total, int) or total <= 0:
            raise ErrorValidacion("El total de la reserva debe ser mayor que cero.")
        self.id = id_reserva
        self.id_cliente = id_cliente
        self.id_paquete = id_paquete
        self.cantidad_personas = cantidad_personas
        self.total = total
        self.fecha_emision = ((fecha_emision or date.today()).isoformat()
                              if isinstance(fecha_emision, date) or fecha_emision is None
                              else fecha_emision)
        self.estado = EstadoReserva(estado)
        self.id_confirmado_por = id_confirmado_por
        self.nombre_paquete = nombre_paquete

    def confirmar(self, id_administrador):
        if self.estado is not EstadoReserva.PENDIENTE:
            raise ErrorNegocio("Solo se pueden confirmar reservas pendientes.")
        self.estado = EstadoReserva.CONFIRMADA
        self.id_confirmado_por = id_administrador

    def cancelar(self):
        if self.estado is EstadoReserva.CANCELADA:
            raise ErrorNegocio("La reserva ya está cancelada.")
        self.estado = EstadoReserva.CANCELADA