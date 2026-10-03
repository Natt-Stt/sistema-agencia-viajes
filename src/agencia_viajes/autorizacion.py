"""Control de acceso por rol (RNF04, RN08, R11).

Autenticación = "¿quién eres?"  ->  ServicioAutenticacion.iniciar_sesion
Autorización  = "¿puedes hacer esto?" -> estas funciones.

Se exige en la capa de SERVICIOS, no solo en el menú: si mañana alguien agrega una
interfaz web y olvida ocultar un botón, el servicio igual rechaza la acción.
"""
from .errores import ErrorAutorizacion
from .models.administrador import Administrador
from .models.cliente import Cliente


def exigir_administrador(actor) -> None:
    if not isinstance(actor, Administrador):
        raise ErrorAutorizacion("No tienes permisos para realizar esta acción.")


def exigir_cliente(actor) -> None:
    if not isinstance(actor, Cliente):
        raise ErrorAutorizacion("No tienes permisos para realizar esta acción.")
