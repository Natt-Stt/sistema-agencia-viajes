"""Entidad Paquete: composición de destinos, cálculo y publicación de precio."""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum

from ..errores import ErrorValidacion


class EstadoPaquete(str, Enum):
    BORRADOR = "BORRADOR"
    PUBLICADO = "PUBLICADO"


def _fecha_iso(valor, etiqueta):
    if isinstance(valor, date):
        return valor.isoformat()
    if not isinstance(valor, str):
        raise ErrorValidacion(f"{etiqueta} debe ser una fecha válida (AAAA-MM-DD).")
    try:
        fecha = date.fromisoformat(valor)
    except ValueError:
        raise ErrorValidacion(f"{etiqueta} debe ser una fecha válida (AAAA-MM-DD).") from None
    if fecha.isoformat() != valor:
        raise ErrorValidacion(f"{etiqueta} debe usar el formato AAAA-MM-DD.")
    return valor


class Paquete:
    def __init__(self, nombre, fecha_salida, fecha_regreso, cupo_maximo,
                 destinos, margen=0.20, temporada="", precio_por_persona=None,
                 estado=EstadoPaquete.BORRADOR, id_paquete=None):
        self._id = id_paquete
        self.nombre = nombre
        self.fecha_salida = fecha_salida
        self.fecha_regreso = fecha_regreso
        self.cupo_maximo = cupo_maximo
        self.margen = margen
        self.temporada = temporada
        self.destinos = destinos
        self.estado = estado
        self.precio_por_persona = (precio_por_persona if precio_por_persona is not None
                                   else self.calcular_precio())

    @property
    def id(self):
        return self._id

    def asignar_id(self, nuevo_id):
        if self._id is not None:
            raise ErrorValidacion("El paquete ya tiene un identificador.")
        self._id = nuevo_id

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or not valor.strip() or len(valor.strip()) > 100:
            raise ErrorValidacion("El nombre del paquete es obligatorio (máximo 100 caracteres).")
        self._nombre = valor.strip()

    @property
    def fecha_salida(self):
        return self._fecha_salida

    @fecha_salida.setter
    def fecha_salida(self, valor):
        self._fecha_salida = _fecha_iso(valor, "La fecha de salida")
        if hasattr(self, "_fecha_regreso") and self._fecha_regreso <= self._fecha_salida:
            raise ErrorValidacion("La fecha de regreso debe ser posterior a la salida.")

    @property
    def fecha_regreso(self):
        return self._fecha_regreso

    @fecha_regreso.setter
    def fecha_regreso(self, valor):
        self._fecha_regreso = _fecha_iso(valor, "La fecha de regreso")
        if hasattr(self, "_fecha_salida") and self._fecha_regreso <= self._fecha_salida:
            raise ErrorValidacion("La fecha de regreso debe ser posterior a la salida.")

    @property
    def cupo_maximo(self):
        return self._cupo_maximo

    @cupo_maximo.setter
    def cupo_maximo(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ErrorValidacion("El cupo máximo debe ser un entero mayor que cero.")
        self._cupo_maximo = valor

    @property
    def margen(self):
        return self._margen

    @margen.setter
    def margen(self, valor):
        if isinstance(valor, bool):
            raise ErrorValidacion("El margen debe ser un número no negativo.")
        try:
            porcentaje = Decimal(str(valor))
        except (InvalidOperation, ValueError):
            raise ErrorValidacion("El margen debe ser un número no negativo.") from None
        if not porcentaje.is_finite() or porcentaje < 0:
            raise ErrorValidacion("El margen debe ser un número no negativo.")
        self._margen = float(porcentaje)

    @property
    def temporada(self):
        return self._temporada

    @temporada.setter
    def temporada(self, valor):
        if valor is None:
            valor = ""
        if not isinstance(valor, str) or len(valor.strip()) > 100:
            raise ErrorValidacion("La temporada no puede superar 100 caracteres.")
        self._temporada = valor.strip()

    @property
    def destinos(self):
        return self._destinos

    @destinos.setter
    def destinos(self, valor):
        if not isinstance(valor, (list, tuple)) or not 2 <= len(valor) <= 5:
            raise ErrorValidacion("Un paquete debe incluir entre 2 y 5 destinos.")
        ids = [destino.id for destino in valor]
        if any(id_destino is None for id_destino in ids) or len(set(ids)) != len(ids):
            raise ErrorValidacion("Los destinos deben estar guardados y no repetirse.")
        self._destinos = list(valor)

    @property
    def estado(self):
        return self._estado

    @estado.setter
    def estado(self, valor):
        try:
            self._estado = EstadoPaquete(valor)
        except ValueError:
            raise ErrorValidacion("El estado del paquete no es válido.") from None

    @property
    def precio_por_persona(self):
        return self._precio_por_persona

    @precio_por_persona.setter
    def precio_por_persona(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ErrorValidacion("El precio por persona debe ser un entero mayor que cero.")
        self._precio_por_persona = valor

    def calcular_precio(self):
        costo = sum(destino.costo_base for destino in self._destinos)
        precio = Decimal(costo) * (Decimal("1") + Decimal(str(self._margen)))
        return int(precio.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def publicar(self):
        self.estado = EstadoPaquete.PUBLICADO