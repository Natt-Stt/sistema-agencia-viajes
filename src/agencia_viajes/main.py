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
from .repositories.repositorio_paquetes import RepositorioPaquetes
from .repositories.repositorio_reservas import RepositorioReservas
from .repositories.repositorio_usuarios import RepositorioUsuarios
from .seguridad import cargar_cifrador
from .services.servicio_autenticacion import ServicioAutenticacion
from .services.servicio_destinos import ELIMINADO, ServicioDestinos
from .services.servicio_paquetes import ServicioPaquetes
from .services.servicio_reservas import ServicioReservas


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


def mostrar_paquetes(paquetes) -> None:
    if not paquetes:
        print("No hay paquetes para mostrar.")
        return
    print(f"{'ID':<5}{'Paquete':<30}{'Salida':<13}{'Precio/persona':<18}{'Cupo':<12}Estado")
    print("-" * 100)
    for paquete, disponible in paquetes:
        print(f"{paquete.id:<5}{paquete.nombre:<30}{paquete.fecha_salida:<13}"
              f"{formatear_pesos(paquete.precio_por_persona):<18}"
              f"{disponible}/{paquete.cupo_maximo:<7}{paquete.estado.value}")
        print("      Destinos: " + ", ".join(destino.nombre for destino in paquete.destinos))


def mostrar_reservas(reservas) -> None:
    if not reservas:
        print("No hay reservas registradas.")
        return
    print(f"{'ID':<5}{'Paquete':<30}{'Personas':<11}{'Total':<15}{'Fecha':<13}Estado")
    print("-" * 85)
    for reserva in reservas:
        print(f"{reserva.id:<5}{(reserva.nombre_paquete or ''):<30}"
              f"{reserva.cantidad_personas:<11}{formatear_pesos(reserva.total):<15}"
              f"{reserva.fecha_emision:<13}{reserva.estado.value}")


def _pedir_ids_destinos():
    texto = input("IDs de destinos (separados por espacios): ").strip()
    if not texto:
        raise ErrorValidacion("Debes indicar entre 2 y 5 destinos.")
    return [convertir_entero(parte, "El ID del destino") for parte in texto.split()]


def opcion_crear_paquete(servicio_paquetes, servicio_destinos, admin):
    print("Destinos disponibles:")
    mostrar_destinos(servicio_destinos.listar(admin, solo_disponibles=True))
    ids = _pedir_ids_destinos()
    nombre = input("Nombre del paquete: ")
    salida = input("Fecha de salida (AAAA-MM-DD): ").strip()
    regreso = input("Fecha de regreso (AAAA-MM-DD): ").strip()
    cupo = pedir_entero("Cupo máximo: ", "El cupo máximo")
    margen_texto = input("Margen porcentual [20]: ").strip()
    try:
        margen = float(margen_texto or "20") / 100
    except ValueError:
        raise ErrorValidacion("El margen debe ser un número no negativo.") from None
    temporada = input("Temporada (opcional): ").strip()
    paquete = servicio_paquetes.crear(admin, nombre, salida, regreso, cupo, ids,
                                      margen=margen, temporada=temporada)
    print(f"Paquete borrador creado con ID {paquete.id}; precio estimado "
          f"{formatear_pesos(paquete.precio_por_persona)} por persona.")


def opcion_modificar_paquete(servicio_paquetes, servicio_destinos, admin):
    id_paquete = pedir_entero("ID del paquete borrador: ", "El ID")
    print("Deja vacío lo que no quieras cambiar.")
    datos = {
        "nombre": pedir_opcional_texto("Nuevo nombre: "),
        "fecha_salida": pedir_opcional_texto("Nueva fecha de salida (AAAA-MM-DD): "),
        "fecha_regreso": pedir_opcional_texto("Nueva fecha de regreso (AAAA-MM-DD): "),
        "cupo_maximo": pedir_opcional_entero("Nuevo cupo máximo: ", "El cupo máximo"),
        "temporada": pedir_opcional_texto("Nueva temporada: "),
    }
    margen = input("Nuevo margen porcentual: ").strip()
    if margen:
        try:
            datos["margen"] = float(margen) / 100
        except ValueError:
            raise ErrorValidacion("El margen debe ser un número no negativo.") from None
    cambiar_destinos = input("¿Cambiar destinos? (s/N): ").strip().lower()
    if cambiar_destinos == "s":
        mostrar_destinos(servicio_destinos.listar(admin, solo_disponibles=True))
        datos["ids_destinos"] = _pedir_ids_destinos()
    servicio_paquetes.modificar_borrador(
        admin, id_paquete, **{clave: valor for clave, valor in datos.items() if valor is not None}
    )
    print("Borrador actualizado.")


def menu_administrador(admin, destinos: ServicioDestinos,
                       paquetes: ServicioPaquetes, reservas: ServicioReservas) -> None:
    while True:
        print(f"\n=== Panel de administración · {admin.nombre} ===")
        print("1. Registrar destino")
        print("2. Listar destinos")
        print("3. Modificar destino")
        print("4. Retirar destino")
        print("5. Crear paquete borrador")
        print("6. Modificar paquete borrador")
        print("7. Publicar paquete")
        print("8. Listar paquetes")
        print("9. Consultar reservas")
        print("10. Confirmar reserva")
        print("11. Cancelar reserva")
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
            elif opcion == "5":
                opcion_crear_paquete(paquetes, destinos, admin)
            elif opcion == "6":
                opcion_modificar_paquete(paquetes, destinos, admin)
            elif opcion == "7":
                id_paquete = pedir_entero("ID del paquete a publicar: ", "El ID")
                paquete = paquetes.publicar(admin, id_paquete)
                print(f"Paquete publicado a {formatear_pesos(paquete.precio_por_persona)} por persona.")
            elif opcion == "8":
                mostrar_paquetes(paquetes.listar(admin))
            elif opcion == "9":
                mostrar_reservas(reservas.listar_para_administrador(admin))
            elif opcion == "10":
                id_reserva = pedir_entero("ID de la reserva a confirmar: ", "El ID")
                reservas.confirmar(admin, id_reserva)
                print("Reserva confirmada.")
            elif opcion == "11":
                id_reserva = pedir_entero("ID de la reserva a cancelar: ", "El ID")
                reservas.cancelar(admin, id_reserva)
                print("Reserva cancelada.")
            elif opcion == "0":
                print("Sesión cerrada.")
                return
            else:
                print("Opción no válida.")
        except ErrorAgencia as error:
            print(f"Error: {error}")


# -------------------------------------------------------------- panel de cliente
def menu_cliente(cliente, paquetes: ServicioPaquetes, reservas: ServicioReservas) -> None:
    while True:
        print(f"\n=== Bienvenido/a, {cliente.nombre} ===")
        print("1. Ver mis datos")
        print("2. Consultar paquetes publicados")
        print("3. Reservar paquete")
        print("4. Consultar mi historial")
        print("5. Cancelar reserva")
        print("0. Cerrar sesión")
        opcion = input("Elige una opción: ").strip()
        try:
            if opcion == "1":
                print(f"Correo:   {cliente.correo}")
                print(f"RUT:      {cliente.rut_enmascarado()}")
                print(f"Teléfono: {cliente.telefono_enmascarado()}")
            elif opcion == "0":
                print("Sesión cerrada.")
                return
            elif opcion == "2":
                mostrar_paquetes(paquetes.listar_publicados(cliente))
            elif opcion == "3":
                disponibles = paquetes.listar_publicados(cliente)
                mostrar_paquetes(disponibles)
                id_paquete = pedir_entero("ID del paquete: ", "El ID")
                personas = pedir_entero("Cantidad de personas: ", "La cantidad de personas")
                reserva = reservas.reservar(cliente, id_paquete, personas)
                print(f"Reserva {reserva.id} registrada por {formatear_pesos(reserva.total)}. "
                      "Queda pendiente de confirmación.")
            elif opcion == "4":
                mostrar_reservas(reservas.historial(cliente))
            elif opcion == "5":
                mostrar_reservas(reservas.historial(cliente))
                id_reserva = pedir_entero("ID de la reserva a cancelar: ", "El ID")
                reservas.cancelar(cliente, id_reserva)
                print("Reserva cancelada.")
            else:
                print("Opción no válida.")
        except ErrorAgencia as error:
            print(f"Error: {error}")


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


def opcion_iniciar_sesion(auth: ServicioAutenticacion, destinos: ServicioDestinos,
                           paquetes: ServicioPaquetes, reservas: ServicioReservas) -> None:
    correo = input("Correo electrónico: ")
    password = getpass("Contraseña: ")          # getpass no muestra lo que escribes
    usuario = auth.iniciar_sesion(correo, password)
    if isinstance(usuario, Administrador):
        menu_administrador(usuario, destinos, paquetes, reservas)
    else:
        menu_cliente(usuario, paquetes, reservas)


def menu_principal(auth: ServicioAutenticacion, destinos: ServicioDestinos,
                   paquetes: ServicioPaquetes, reservas: ServicioReservas) -> None:
    while True:
        print("\n=== Viajes Aventura ===")
        print("1. Iniciar sesión")
        print("2. Registrarse")
        print("0. Salir")
        opcion = input("Elige una opción: ").strip()
        try:
            if opcion == "1":
                opcion_iniciar_sesion(auth, destinos, paquetes, reservas)
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
        repositorio_paquetes = RepositorioPaquetes(conexion)
        repositorio_reservas = RepositorioReservas(conexion)
        paquetes = ServicioPaquetes(repositorio_paquetes, RepositorioDestinos(conexion),
                        repositorio_reservas)
        reservas = ServicioReservas(repositorio_reservas, repositorio_paquetes)
        menu_principal(auth, destinos, paquetes, reservas)
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
