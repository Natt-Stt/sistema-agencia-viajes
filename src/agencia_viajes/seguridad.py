"""Seguridad criptográfica: hash de contraseñas (bcrypt) y cifrado de datos (Fernet).

Dos herramientas distintas para dos problemas distintos:

* HASH  (bcrypt)  -> contraseñas. Es de UNA sola vía: no se puede recuperar la
  contraseña original, solo comprobar si una escrita coincide (R10).
* CIFRADO (Fernet) -> RUT y teléfono. Es de DOS vías: se cifra para guardar y se
  descifra con una clave cuando hay que mostrarlo al propio cliente (R17).

Ambas librerías vienen de PyPI (repositorio oficial de Python).
"""
import os
from pathlib import Path

import bcrypt
from cryptography.fernet import Fernet, InvalidToken

from .errores import ErrorNegocio, ErrorValidacion

# "Costo" de bcrypt: cada +1 duplica el tiempo de cálculo. 12 ≈ 0,25 s por intento,
# imperceptible para una persona pero muy caro para un atacante que prueba millones.
COSTO_BCRYPT = 12
_MAX_BYTES_BCRYPT = 72


def hashear_password(password: str) -> str:
    datos = password.encode("utf-8")
    if len(datos) > _MAX_BYTES_BCRYPT:
        raise ErrorValidacion("La contraseña es demasiado larga (máximo 72 caracteres).")
    # gensalt() crea una "sal" aleatoria nueva y bcrypt la incrusta en el hash:
    # dos usuarios con la misma contraseña obtienen hashes distintos.
    return bcrypt.hashpw(datos, bcrypt.gensalt(rounds=COSTO_BCRYPT)).decode("ascii")


def verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("ascii"))
    except (ValueError, TypeError, AttributeError):
        return False


_hash_ficticio = None


def verificar_password_ficticia(password) -> None:
    """Gasta el mismo tiempo que una verificación real.

    Si el correo NO existe, el login respondería más rápido que si existe, y un
    atacante podría averiguar qué correos están registrados midiendo el tiempo
    (enumeración de usuarios). Verificar contra un hash falso iguala los tiempos.
    """
    global _hash_ficticio
    if _hash_ficticio is None:
        _hash_ficticio = hashear_password("Contraseña-ficticia-1")
    verificar_password(password if isinstance(password, str) else "", _hash_ficticio)


class CifradorDatos:
    """Cifrado simétrico autenticado (Fernet = AES-128-CBC + HMAC-SHA256).

    'Autenticado' significa que además de ocultar el dato, detecta si alguien lo
    alteró: confidencialidad e integridad.
    """

    def __init__(self, clave: bytes):
        try:
            self._fernet = Fernet(clave)
        except (ValueError, TypeError):
            raise ErrorNegocio("La clave de cifrado configurada no es válida.") from None

    @staticmethod
    def generar_clave() -> bytes:
        return Fernet.generate_key()

    def cifrar(self, texto: str) -> str:
        return self._fernet.encrypt(texto.encode("utf-8")).decode("ascii")

    def descifrar(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError):
            raise ErrorNegocio("No fue posible leer un dato protegido.") from None


VARIABLE_CLAVE = "AGENCIA_CLAVE_CIFRADO"
RUTA_CLAVE_POR_DEFECTO = Path("data") / "clave.key"


def cargar_cifrador(ruta_clave=RUTA_CLAVE_POR_DEFECTO) -> CifradorDatos:
    """Obtiene la clave de cifrado. La clave NUNCA va dentro de la base de datos.

    Prioridad: 1) variable de entorno AGENCIA_CLAVE_CIFRADO  2) archivo  3) se crea.
    Si pierdes la clave, los RUT y teléfonos guardados no se pueden recuperar.
    """
    clave_entorno = os.environ.get(VARIABLE_CLAVE)
    if clave_entorno:
        return CifradorDatos(clave_entorno.strip().encode("ascii"))
    ruta = Path(ruta_clave)
    if ruta.exists():
        return CifradorDatos(ruta.read_bytes().strip())
    ruta.parent.mkdir(parents=True, exist_ok=True)
    clave = CifradorDatos.generar_clave()
    ruta.write_bytes(clave)
    try:
        os.chmod(ruta, 0o600)      # solo el dueño puede leerla (en Windows puede no aplicar)
    except OSError:
        pass
    return CifradorDatos(clave)
