"""Clase abstracta Usuario (abstracción + herencia).

'Abstracta' = no se puede crear un Usuario a secas; solo sus hijos Cliente y
Administrador. Aquí va lo que tienen en común (nombre, correo, contraseña).
Lo que cada hijo hace distinto (rol, resumen) se declara @abstractmethod: es
obligatorio implementarlo, y de ahí sale el polimorfismo.

La contraseña NUNCA entra en claro a esta clase: recibe solo el hash (R10).
"""
from abc import ABC, abstractmethod

from .. import seguridad
from ..errores import ErrorValidacion
from ..validaciones import validar_correo, validar_nombre


class Usuario(ABC):
    def __init__(self, nombre, correo, password_hash, id_usuario=None):
        self._id = id_usuario
        self.nombre = nombre
        self.correo = correo
        if not isinstance(password_hash, str) or not password_hash:
            raise ErrorValidacion("Falta el hash de la contraseña.")
        self._password_hash = password_hash

    @property
    def id(self):
        return self._id

    def asignar_id(self, nuevo_id: int) -> None:
        if self._id is not None:
            raise ErrorValidacion("El usuario ya tiene un identificador.")
        self._id = nuevo_id

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor) -> None:
        self._nombre = validar_nombre(valor)

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor) -> None:
        self._correo = validar_correo(valor)

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    @abstractmethod
    def rol(self) -> str:
        """'CLIENTE' o 'ADMINISTRADOR'."""

    @abstractmethod
    def resumen(self) -> str:
        """Texto seguro para listados: jamás incluye RUT ni teléfono (R17)."""

    def verificar_password(self, password: str) -> bool:
        return seguridad.verificar_password(password, self._password_hash)

    def __repr__(self) -> str:
        # Sin hash, sin RUT, sin teléfono: un repr se filtra fácil a logs y errores.
        return f"{type(self).__name__}(id={self._id}, correo={self._correo!r})"
