"""Crea un usuario Administrador (supuesto S7).

No existe "registrarse como administrador" en el sistema: eso permitiría que
cualquiera se otorgara privilegios. Los socios crean sus cuentas con este script,
que solo puede ejecutar quien tiene acceso al computador donde está el sistema.

Ejecutar desde la raíz:   python -m src.agencia_viajes.crear_admin
"""
from getpass import getpass

from .database import crear_esquema, obtener_conexion
from .errores import ErrorAgencia
from .repositories.repositorio_usuarios import RepositorioUsuarios
from .seguridad import cargar_cifrador
from .services.servicio_autenticacion import ServicioAutenticacion


def main() -> None:
    print("=== Crear administrador ===")
    nombre = input("Nombre completo: ")
    correo = input("Correo electrónico: ")
    password = getpass("Contraseña: ")
    repetida = getpass("Repite la contraseña: ")
    if password != repetida:
        print("Error: las contraseñas no coinciden.")
        return

    conexion = obtener_conexion()
    try:
        crear_esquema(conexion)
        auth = ServicioAutenticacion(RepositorioUsuarios(conexion, cargar_cifrador()))
        auth.crear_administrador(nombre, correo, password)
        print("Administrador creado correctamente.")
    except ErrorAgencia as error:
        print(f"Error: {error}")
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
