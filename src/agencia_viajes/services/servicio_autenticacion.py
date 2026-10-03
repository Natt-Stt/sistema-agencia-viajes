"""Registro e inicio de sesión (RF01, RF02, R9, R10, R11).

Buenas prácticas aplicadas:
* Mensaje ÚNICO ante cualquier fallo de login ("Credenciales inválidas."): no revela
  si el correo existe o si solo la contraseña estaba mal.
* Tiempo igualado cuando el correo no existe (evita enumerar usuarios por tiempo).
* Bloqueo temporal tras varios fallos seguidos (frena la fuerza bruta).
"""
import math
import time

from .. import seguridad
from ..errores import ErrorAutenticacion, ErrorValidacion
from ..models.administrador import Administrador
from ..models.cliente import Cliente
from ..models.usuario import Usuario
from ..repositories.repositorio_usuarios import RepositorioUsuarios
from ..validaciones import validar_correo, validar_password_fuerte


class ServicioAutenticacion:
    MAX_INTENTOS = 5          # supuesto S11
    SEGUNDOS_BLOQUEO = 60

    def __init__(self, repositorio: RepositorioUsuarios, reloj=time.monotonic):
        self._repo = repositorio
        self._reloj = reloj              # inyectable para poder probar el bloqueo
        self._fallos: dict[str, tuple[int, float]] = {}

    # ---- registro -----------------------------------------------------------
    def registrar_cliente(self, nombre, rut, correo, telefono, password) -> Cliente:
        """RF01. Valida, hashea la contraseña y guarda (RUT y teléfono cifrados)."""
        password = validar_password_fuerte(password)
        cliente = Cliente(nombre, rut, correo, telefono,
                          seguridad.hashear_password(password))
        return self._repo.guardar(cliente)

    def crear_administrador(self, nombre, correo, password) -> Administrador:
        """S7: lo usa el script crear_admin.py; no existe auto-registro de admins."""
        password = validar_password_fuerte(password)
        admin = Administrador(nombre, correo, seguridad.hashear_password(password))
        return self._repo.guardar(admin)

    # ---- inicio de sesión ---------------------------------------------------
    def iniciar_sesion(self, correo, password) -> Usuario:
        """RF02. Devuelve el Usuario (Cliente o Administrador) o lanza ErrorAutenticacion."""
        clave = self._clave_intentos(correo)
        self._verificar_bloqueo(clave)

        usuario = self._buscar_usuario(correo)
        if usuario is None:
            seguridad.verificar_password_ficticia(password)
            valido = False
        else:
            valido = isinstance(password, str) and usuario.verificar_password(password)

        if not valido:
            self._registrar_fallo(clave)
            raise ErrorAutenticacion("Credenciales inválidas.")
        self._fallos.pop(clave, None)
        return usuario

    # ---- apoyo interno ------------------------------------------------------
    def _buscar_usuario(self, correo) -> Usuario | None:
        try:
            return self._repo.buscar_por_correo(validar_correo(correo))
        except ErrorValidacion:
            return None       # un correo mal escrito se trata igual que uno inexistente

    @staticmethod
    def _clave_intentos(correo) -> str:
        texto = correo.strip().lower() if isinstance(correo, str) else ""
        return texto[:254]    # tope para que nadie infle la memoria con claves enormes

    def _verificar_bloqueo(self, clave: str) -> None:
        registro = self._fallos.get(clave)
        if registro is None:
            return
        cantidad, desbloqueo = registro
        if cantidad >= self.MAX_INTENTOS:
            restante = desbloqueo - self._reloj()
            if restante > 0:
                raise ErrorAutenticacion(
                    f"Demasiados intentos fallidos. Intenta de nuevo en {math.ceil(restante)} segundos.")
            del self._fallos[clave]       # el bloqueo venció: se parte de cero

    def _registrar_fallo(self, clave: str) -> None:
        cantidad, _ = self._fallos.get(clave, (0, 0.0))
        cantidad += 1
        desbloqueo = self._reloj() + self.SEGUNDOS_BLOQUEO if cantidad >= self.MAX_INTENTOS else 0.0
        self._fallos[clave] = (cantidad, desbloqueo)
