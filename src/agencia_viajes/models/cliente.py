"""Cliente: usuario que reserva paquetes. Guarda datos sensibles (R17)."""
from ..validaciones import validar_rut, validar_telefono
from .usuario import Usuario


class Cliente(Usuario):
    def __init__(self, nombre, rut, correo, telefono, password_hash, id_usuario=None):
        super().__init__(nombre, correo, password_hash, id_usuario)
        self.rut = rut
        self.telefono = telefono

    @property
    def rut(self) -> str:
        return self._rut

    @rut.setter
    def rut(self, valor) -> None:
        self._rut = validar_rut(valor)

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor) -> None:
        self._telefono = validar_telefono(valor)

    @property
    def rol(self) -> str:
        return "CLIENTE"

    def resumen(self) -> str:
        return f"{self.nombre} <{self.correo}>"

    def rut_enmascarado(self) -> str:
        """'12345678-5' -> '******78-5'."""
        cuerpo, dv = self._rut.split("-")
        return "*" * (len(cuerpo) - 2) + cuerpo[-2:] + "-" + dv

    def telefono_enmascarado(self) -> str:
        """'+56912345678' -> '**********678'."""
        return "*" * (len(self._telefono) - 3) + self._telefono[-3:]
