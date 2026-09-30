"""Entidad Destino (R1, R2).

Encapsulamiento: los atributos son "privados" (_nombre, _costo_base...) y solo se
cambian a través de propiedades (@property) que VALIDAN el valor. Así es
imposible que exista un Destino con costo cero o sin nombre, sin importar desde
dónde se cree o se modifique.
"""
from ..errores import ErrorValidacion


def _texto_obligatorio(valor, etiqueta: str, maximo: int) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ErrorValidacion(f"{etiqueta} es obligatorio.")
    valor = valor.strip()
    if len(valor) > maximo:
        raise ErrorValidacion(f"{etiqueta} no puede superar {maximo} caracteres.")
    return valor


def _entero_positivo(valor, etiqueta: str) -> int:
    # bool es subclase de int en Python (True == 1): se excluye explícitamente.
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ErrorValidacion(f"{etiqueta} debe ser un número entero.")
    if valor <= 0:
        raise ErrorValidacion(f"{etiqueta} debe ser mayor que cero.")
    return valor


class Destino:
    def __init__(self, nombre, zona, duracion_dias, costo_base,
                 descripcion="", disponible=True, id_destino=None):
        self._id = id_destino
        # Se asignan con self.x = ... para que corran los setters con validación.
        self.nombre = nombre
        self.zona = zona
        self.descripcion = descripcion
        self.duracion_dias = duracion_dias
        self.costo_base = costo_base
        self._disponible = bool(disponible)

    # --- identificador: solo lectura, se asigna una vez al guardar ---------
    @property
    def id(self):
        return self._id

    def asignar_id(self, nuevo_id: int) -> None:
        if self._id is not None:
            raise ErrorValidacion("El destino ya tiene un identificador.")
        self._id = nuevo_id

    # --- atributos con validación -------------------------------------------
    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor) -> None:
        self._nombre = _texto_obligatorio(valor, "El nombre del destino", 100)

    @property
    def zona(self) -> str:
        return self._zona

    @zona.setter
    def zona(self, valor) -> None:
        self._zona = _texto_obligatorio(valor, "La zona", 100)

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor) -> None:
        # Supuesto: la descripción es opcional (puede quedar vacía).
        if valor is None:
            valor = ""
        if not isinstance(valor, str) or len(valor.strip()) > 500:
            raise ErrorValidacion("La descripción no puede superar 500 caracteres.")
        self._descripcion = valor.strip()

    @property
    def duracion_dias(self) -> int:
        return self._duracion_dias

    @duracion_dias.setter
    def duracion_dias(self, valor) -> None:
        self._duracion_dias = _entero_positivo(valor, "La duración en días")

    @property
    def costo_base(self) -> int:
        return self._costo_base

    @costo_base.setter
    def costo_base(self, valor) -> None:
        # R2: costo > 0. Se guarda como entero (pesos chilenos no usan decimales);
        # con float se acumularían errores de redondeo al sumar precios.
        self._costo_base = _entero_positivo(valor, "El costo base")

    @property
    def disponible(self) -> bool:
        return self._disponible

    def marcar_no_disponible(self) -> None:
        self._disponible = False

    def __repr__(self) -> str:
        return f"Destino(id={self._id}, nombre={self._nombre!r}, costo_base={self._costo_base})"
