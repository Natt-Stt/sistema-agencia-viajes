"""Administrador: socio que gestiona catálogo, paquetes y reservas."""
from .usuario import Usuario


class Administrador(Usuario):
    @property
    def rol(self) -> str:
        return "ADMINISTRADOR"

    def resumen(self) -> str:
        return f"{self.nombre} <{self.correo}> (administrador)"
