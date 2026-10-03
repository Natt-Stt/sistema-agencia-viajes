"""Validación de TODO dato ingresado por el usuario (RNF06).

Regla de oro: nunca confiar en lo que escribe el usuario. Cada función revisa el
dato, lo NORMALIZA (formato único para guardarlo) y lanza ErrorValidacion si no
sirve. Los mensajes de error jamás repiten el valor ingresado: así un RUT o un
teléfono nunca aparecen en un mensaje de error (R17).
"""
import re

from .errores import ErrorValidacion

_LETRAS = "A-Za-zÁÉÍÓÚÜÑáéíóúüñ"
_PATRON_NOMBRE = re.compile(rf"^[{_LETRAS}][{_LETRAS}' .\-]{{1,99}}$")
_PATRON_CORREO = re.compile(
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$")
_PATRON_RUT = re.compile(r"^(\d{7,8})-?([\dK])$")
_PATRON_TELEFONO = re.compile(r"^\+?\d{8,15}$")


def validar_nombre(valor) -> str:
    if not isinstance(valor, str) or not _PATRON_NOMBRE.match(valor.strip()):
        raise ErrorValidacion(
            "El nombre debe tener entre 2 y 100 letras (se permiten espacios, guiones y apóstrofes).")
    return " ".join(valor.split())


def validar_correo(valor) -> str:
    """Devuelve el correo en minúsculas. R9: el correo identifica al cliente."""
    if not isinstance(valor, str):
        raise ErrorValidacion("El correo electrónico no es válido.")
    correo = valor.strip().lower()
    if len(correo) > 254 or not _PATRON_CORREO.match(correo):
        raise ErrorValidacion("El correo electrónico no es válido.")
    return correo


def _digito_verificador(cuerpo: str) -> str:
    """Algoritmo módulo 11 del RUT chileno."""
    suma, multiplicador = 0, 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def validar_rut(valor) -> str:
    """Acepta '12.345.678-5', '12345678-5' o '123456785'. Devuelve '12345678-5'."""
    if not isinstance(valor, str):
        raise ErrorValidacion("El RUT ingresado no es válido.")
    limpio = valor.strip().upper().replace(".", "").replace(" ", "")
    coincidencia = _PATRON_RUT.match(limpio)
    if not coincidencia:
        raise ErrorValidacion("El RUT ingresado no es válido.")
    cuerpo, dv = coincidencia.groups()
    if _digito_verificador(cuerpo) != dv:
        raise ErrorValidacion("El RUT ingresado no es válido.")
    return f"{cuerpo}-{dv}"


def validar_telefono(valor) -> str:
    """Supuesto: teléfono de 8 a 15 dígitos, con '+' opcional. Devuelve '+56912345678'."""
    if not isinstance(valor, str):
        raise ErrorValidacion("El teléfono ingresado no es válido.")
    limpio = re.sub(r"[\s\-()]", "", valor.strip())
    if not _PATRON_TELEFONO.match(limpio):
        raise ErrorValidacion("El teléfono ingresado no es válido.")
    return limpio


def validar_password_fuerte(valor) -> str:
    """Política: 8+ caracteres, mayúscula, minúscula y número.

    Máximo 72 BYTES: bcrypt solo procesa los primeros 72, y aceptar más daría una
    falsa sensación de seguridad. La contraseña NO se recorta ni se modifica.
    """
    if not isinstance(valor, str):
        raise ErrorValidacion("La contraseña no es válida.")
    if len(valor) < 8:
        raise ErrorValidacion("La contraseña debe tener al menos 8 caracteres.")
    if len(valor.encode("utf-8")) > 72:
        raise ErrorValidacion("La contraseña es demasiado larga (máximo 72 caracteres).")
    if not (re.search(r"[a-z]", valor) and re.search(r"[A-Z]", valor)
            and re.search(r"\d", valor)):
        raise ErrorValidacion(
            "La contraseña debe incluir mayúsculas, minúsculas y números.")
    return valor
