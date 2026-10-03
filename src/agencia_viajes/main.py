"""Menú de consola: inicio de sesión, registro y paneles por rol (Sprint 2a).

Ejecutar desde la raíz del proyecto:   python -m src.agencia_viajes.main
Primero crea un administrador:         python -m src.agencia_viajes.crear_admin

La "sesión" es simplemente la variable `usuario` que recibe cada menú mientras la
persona está dentro; al volver al menú principal (cerrar sesión) se descarta.
"""
from getpass import getpass

from .database import crear_esquema, obtener_conexion
from .errores import ErrorAgencia, ErrorValidacion
from .models.administrador import Administrador
from .repositories.repositorio_destinos import RepositorioDestinos
from .repositories.repositorio_usuarios import RepositorioUsuarios
from .seguridad import cargar_cifrador
from .services.servicio_autenticacion import ServicioAutenticacion
from .services.servicio_destinos import ELIMINADO, ServicioDestinos


# ---------------------------------------------------------------- utilidades
def formatear_pesos(valor: int) -> str:
    """120000 -> $120.000 (formato chileno)."""
    return "$" + f"{valor:,}".replace(",", ".")


def convertir_entero(texto: str, etiqueta: str) -> int:
    """Acepta '120000' o '120.000'. Rechaza letras, comas y decimales."""
    limpio = texto.strip().replace(".", "")
    if not limpio.isdigit():
        raise ErrorValidacion(f"{etiqueta} debe ser un número entero, sin decimales.")
    return int(limpio)


def pedir_entero(mensaje: str, etiqueta: str) -> int:
    return convertir_entero(input(mensaje), etiqueta)


def pedir_opcional_entero(mensaje: str, etiqueta: str):
    texto = input(mensaje).strip()
    return convertir_entero(texto, etiqueta) if texto else None


def pedir_opcional_texto(mensaje: str):
    texto = input(mensaje).strip()
    return texto if texto else None


# ------------------------------------------------------------ panel de destinos
def mostrar_destinos(destinos) -> None:
    if not destinos:
        print("No hay destinos registrados.")
        return
    print(f"{'ID':<4}{'Nombre':<28}{'Zona':<24}{'Días':<6}{'Costo base':<13}Estado")
    print("-" * 85)
    for d in destinos:
        estado = "Disponible" if d.disponible else "No disponible"
        print(f"{d.id:<4}{d.nombre:<28}{d.zona:<24}{d.duracion_dias:<6}"
              f"{formatear_pesos(d.costo_base):<13}{estado}")


def opcion_registrar(servicio: ServicioDestinos, admin) -> None:
    nombre = input("Nombre: ")
    zona = input("Zona: ")
    descripcion = input("Descripción (opcional): ")
    duracion = pedir_entero("Duración en días: ", "La duración")
    costo = pedir_entero("Costo base por persona (CLP): ", "El costo base")
    destino = servicio.registrar(admin, nombre, zona, duracion, costo, descripcion)
    print(f"Destino registrado con ID {destino.id}.")


def opcion_modificar(servicio: ServicioDestinos, admin) -> None:
    id_destino = pedir_entero("ID del destino a modificar: ", "El ID")
    print("Deja vacío lo que no quieras cambiar.")
    servicio.modificar(
        admin, id_destino,
        nombre=pedir_opcional_texto("Nuevo nombre: "),
        zona=pedir_opcional_texto("Nueva zona: "),
        descripcion=pedir_opcional_texto("Nueva descripción: "),
        duracion_dias=pedir_opcional_entero("Nueva duración en días: ", "La duración"),
        costo_base=pedir_opcional_entero("Nuevo costo base (CLP): ", "El costo base"),
    )
    print("Destino modificado.")


def opcion_retirar(servicio: ServicioDestinos, admin) -> None:
    id_destino = pedir_entero("ID del destino a retirar: ", "El ID")
    resultado = servicio.retirar(admin, id_destino)
    if resultado == ELIMINADO:
        print("El destino no estaba en ningún paquete: fue eliminado.")
    else:
        print("El destino forma parte de paquetes: quedó como NO disponible.")


def menu_administrador(admin, destinos: ServicioDestinos) -> None:
    while True:
        print(f"\n=== Panel de administración · {admin.nombre} ===")
        print("1. Registrar destino")
        print("2. Listar destinos")
        print("3. Modificar destino")
        print("4. Retirar destino")
        print("0. Cerrar sesión")
        opcion = input("Elige una opción: ").strip()
        try:
            if opcion == "1":
                opcion_registrar(destinos, admin)
            elif opcion == "2":
                mostrar_destinos(destinos.listar(admin))
            elif opcion == "3":
                opcion_modificar(destinos, admin)
            elif opcion == "4":
                opcion_retirar(destinos, admin)
            elif opcion == "0":
                print("Sesión cerrada.")
                return
            else:
                print("Opción no válida.")
        except ErrorAgencia as error:
            print(f"Error: {error}")


# -------------------------------------------------------------- panel de cliente
def menu_cliente(cliente) -> None:
    while True:
        print(f"\n=== Bienvenido/a, {cliente.nombre} ===")
        print("1. Ver mis datos")
        print("0. Cerrar sesión")
        opcion = input("Elige una opción: ").strip()
        if opcion == "1":
            # Es SU propio perfil, pero igual se muestran enmascarados (R17).
            print(f"Correo:   {cliente.correo}")
            print(f"RUT:      {cliente.rut_enmascarado()}")
            print(f"Teléfono: {cliente.telefono_enmascarado()}")
        elif opcion == "0":
            print("Sesión cerrada.")
            return
        else:
            print("Opción no válida.")
        # (Sprint 2b: aquí irán consultar paquetes, reservar y ver historial.)


# ------------------------------------------------------------- menú principal
def pedir_password_nueva() -> str:
    clave = getpass("Contraseña: ")
    repetida = getpass("Repite la contraseña: ")
    if clave != repetida:
        raise ErrorValidacion("Las contraseñas no coinciden.")
    return clave


def opcion_registrarse(auth: ServicioAutenticacion) -> None:
    print("--- Crear cuenta de cliente ---")
    nombre = input("Nombre completo: ")
    rut = input("RUT (ej. 12.345.678-5): ")
    correo = input("Correo electrónico: ")
    telefono = input("Teléfono: ")
    password = pedir_password_nueva()
    auth.registrar_cliente(nombre, rut, correo, telefono, password)
    print("Cuenta creada. Ahora puedes iniciar sesión.")


def opcion_iniciar_sesion(auth: ServicioAutenticacion, destinos: ServicioDestinos) -> None:
    correo = input("Correo electrónico: ")
    password = getpass("Contraseña: ")          # getpass no muestra lo que escribes
    usuario = auth.iniciar_sesion(correo, password)
    if isinstance(usuario, Administrador):
        menu_administrador(usuario, destinos)
    else:
        menu_cliente(usuario)


def menu_principal(auth: ServicioAutenticacion, destinos: ServicioDestinos) -> None:
    while True:
        print("\n=== Viajes Aventura ===")
        print("1. Iniciar sesión")
        print("2. Registrarse")
        print("0. Salir")
        opcion = input("Elige una opción: ").strip()
        try:
            if opcion == "1":
                opcion_iniciar_sesion(auth, destinos)
            elif opcion == "2":
                opcion_registrarse(auth)
            elif opcion == "0":
                print("Hasta luego.")
                return
            else:
                print("Opción no válida.")
        except ErrorAgencia as error:
            # Solo errores controlados: los mensajes ya son seguros (sin RUT ni teléfono).
            print(f"Error: {error}")


def main() -> None:
    conexion = obtener_conexion()
    try:
        crear_esquema(conexion)
        cifrador = cargar_cifrador()
        auth = ServicioAutenticacion(RepositorioUsuarios(conexion, cifrador))
        destinos = ServicioDestinos(RepositorioDestinos(conexion))
        menu_principal(auth, destinos)
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
