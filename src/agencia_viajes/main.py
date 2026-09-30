"""Menú de consola del Sprint 1: gestión de destinos.

AVISO (deuda técnica): en este sprint el menú es accesible sin iniciar sesión.
En el Sprint 2 se protege con autenticación y rol de administrador (RNF04, S6).

Ejecutar desde la raíz del proyecto:   python -m src.agencia_viajes.main
"""
from .database import crear_esquema, obtener_conexion
from .errores import ErrorAgencia, ErrorValidacion
from .repositories.repositorio_destinos import RepositorioDestinos
from .services.servicio_destinos import ELIMINADO, ServicioDestinos


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


def opcion_registrar(servicio: ServicioDestinos) -> None:
    nombre = input("Nombre: ")
    zona = input("Zona: ")
    descripcion = input("Descripción (opcional): ")
    duracion = pedir_entero("Duración en días: ", "La duración")
    costo = pedir_entero("Costo base por persona (CLP): ", "El costo base")
    destino = servicio.registrar(nombre, zona, duracion, costo, descripcion)
    print(f"Destino registrado con ID {destino.id}.")


def opcion_modificar(servicio: ServicioDestinos) -> None:
    id_destino = pedir_entero("ID del destino a modificar: ", "El ID")
    print("Deja vacío lo que no quieras cambiar.")
    servicio.modificar(
        id_destino,
        nombre=pedir_opcional_texto("Nuevo nombre: "),
        zona=pedir_opcional_texto("Nueva zona: "),
        descripcion=pedir_opcional_texto("Nueva descripción: "),
        duracion_dias=pedir_opcional_entero("Nueva duración en días: ", "La duración"),
        costo_base=pedir_opcional_entero("Nuevo costo base (CLP): ", "El costo base"),
    )
    print("Destino modificado.")


def opcion_retirar(servicio: ServicioDestinos) -> None:
    id_destino = pedir_entero("ID del destino a retirar: ", "El ID")
    resultado = servicio.retirar(id_destino)
    if resultado == ELIMINADO:
        print("El destino no estaba en ningún paquete: fue eliminado.")
    else:
        print("El destino forma parte de paquetes: quedó como NO disponible.")


def menu_destinos(servicio: ServicioDestinos) -> None:
    while True:
        print("\n=== Viajes Aventura · Destinos ===")
        print("1. Registrar destino")
        print("2. Listar destinos")
        print("3. Modificar destino")
        print("4. Retirar destino")
        print("0. Salir")
        opcion = input("Elige una opción: ").strip()
        try:
            if opcion == "1":
                opcion_registrar(servicio)
            elif opcion == "2":
                mostrar_destinos(servicio.listar())
            elif opcion == "3":
                opcion_modificar(servicio)
            elif opcion == "4":
                opcion_retirar(servicio)
            elif opcion == "0":
                print("Hasta luego.")
                break
            else:
                print("Opción no válida.")
        except ErrorAgencia as error:
            # Solo se atrapan errores controlados; el mensaje ya es seguro.
            print(f"Error: {error}")


def main() -> None:
    conexion = obtener_conexion()
    try:
        crear_esquema(conexion)
        servicio = ServicioDestinos(RepositorioDestinos(conexion))
        menu_destinos(servicio)
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
