"""Reglas de negocio y autorización de reservas (RF13 a RF17)."""
from datetime import date

from ..autorizacion import exigir_administrador, exigir_cliente
from ..errores import ErrorNegocio, ErrorValidacion
from ..models.reserva import Reserva


class ServicioReservas:
    def __init__(self, repositorio, repositorio_paquetes, reloj=date.today):
        self._repo = repositorio
        self._paquetes = repositorio_paquetes
        self._reloj = reloj

    def reservar(self, cliente, id_paquete, personas):
        exigir_cliente(cliente)
        if cliente.id is None:
            raise ErrorNegocio("La cuenta debe estar guardada para reservar.")
        if isinstance(personas, bool) or not isinstance(personas, int) or personas < 1:
            raise ErrorValidacion("La cantidad de personas debe ser un entero mayor que cero.")
        paquete = self._paquetes.buscar(id_paquete)
        if paquete is None:
            raise ErrorNegocio("El paquete indicado no existe.")
        return self._repo.reservar(
            Reserva(cliente.id, paquete.id, personas,
                    paquete.precio_por_persona * personas, self._reloj()),
            self._reloj().isoformat(),
        )

    def historial(self, cliente):
        exigir_cliente(cliente)
        return self._repo.listar_por_cliente(cliente.id)

    def listar_para_administrador(self, administrador):
        exigir_administrador(administrador)
        return self._repo.listar_todas()

    def cancelar(self, actor, id_reserva):
        reserva = self._obtener(id_reserva)
        if getattr(actor, "rol", None) == "CLIENTE":
            exigir_cliente(actor)
            if actor.id != reserva.id_cliente:
                raise ErrorNegocio("No puedes modificar una reserva ajena.")
        else:
            exigir_administrador(actor)
        reserva.cancelar()
        return self._repo.actualizar(reserva)

    def confirmar(self, administrador, id_reserva):
        exigir_administrador(administrador)
        if administrador.id is None:
            raise ErrorNegocio("La cuenta administradora debe estar guardada para confirmar.")
        reserva = self._obtener(id_reserva)
        reserva.confirmar(administrador.id)
        return self._repo.actualizar(reserva)

    def _obtener(self, id_reserva):
        reserva = self._repo.buscar(id_reserva)
        if reserva is None:
            raise ErrorNegocio("La reserva indicada no existe.")
        return reserva