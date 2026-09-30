"""Excepciones propias del sistema.

Por qué existen: si el código lanzara siempre Exception, no podríamos distinguir
un error del usuario ("costo inválido") de un bug del programa. Con clases
propias, la interfaz atrapa SOLO los errores controlados y muestra un mensaje
limpio, sin exponer detalles internos (RNF05, R17).
"""


class ErrorAgencia(Exception):
    """Base de todos los errores controlados del sistema."""


class ErrorValidacion(ErrorAgencia):
    """Un dato ingresado no cumple el formato o el rango permitido."""


class ErrorNegocio(ErrorAgencia):
    """Se intentó algo que viola una regla de negocio (R1 a R17)."""
