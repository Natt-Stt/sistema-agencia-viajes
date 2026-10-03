"""Pruebas de registro, login y roles (RF01, RF02, R9, R10, R11, R17, RNF03, RNF04)."""
import unittest

from src.agencia_viajes import seguridad
from src.agencia_viajes.database import crear_esquema, obtener_conexion
from src.agencia_viajes.errores import ErrorAutenticacion, ErrorNegocio, ErrorValidacion
from src.agencia_viajes.models.administrador import Administrador
from src.agencia_viajes.models.cliente import Cliente
from src.agencia_viajes.models.usuario import Usuario
from src.agencia_viajes.repositories.repositorio_usuarios import RepositorioUsuarios
from src.agencia_viajes.services.servicio_autenticacion import ServicioAutenticacion

PASSWORD = "Clave-Segura1"


def setUpModule():
    seguridad.COSTO_BCRYPT = 4


class RelojFalso:
    def __init__(self):
        self.ahora = 1000.0

    def __call__(self):
        return self.ahora


class PruebasAutenticacion(unittest.TestCase):
    def setUp(self):
        self.con = obtener_conexion(":memory:")
        crear_esquema(self.con)
        self.cifrador = seguridad.CifradorDatos(seguridad.CifradorDatos.generar_clave())
        self.reloj = RelojFalso()
        self.auth = ServicioAutenticacion(
            RepositorioUsuarios(self.con, self.cifrador), reloj=self.reloj)

    def tearDown(self):
        self.con.close()

    def _registrar_carolina(self, correo="carolina@mail.cl"):
        return self.auth.registrar_cliente(
            "Carolina Reyes", "12.345.678-5", correo, "+56 9 1234 5678", PASSWORD)

    # ---- RF01: registro --------------------------------------------------------
    def test_registro_valido_devuelve_cliente_con_id(self):
        cliente = self._registrar_carolina()
        self.assertIsInstance(cliente, Cliente)
        self.assertIsNotNone(cliente.id)

    def test_r10_la_contrasena_se_guarda_como_hash(self):
        self._registrar_carolina()
        fila = self.con.execute("SELECT password_hash FROM usuarios").fetchone()
        self.assertNotIn(PASSWORD, fila["password_hash"])
        self.assertTrue(fila["password_hash"].startswith("$2"))

    def test_r17_rut_y_telefono_se_guardan_cifrados(self):
        self._registrar_carolina()
        fila = self.con.execute("SELECT rut, telefono FROM usuarios").fetchone()
        self.assertNotIn("12345678", fila["rut"])
        self.assertNotIn("56912345678", fila["telefono"])
        # ...y aun así el sistema los recupera al leer:
        cliente = RepositorioUsuarios(self.con, self.cifrador).buscar_por_correo("carolina@mail.cl")
        self.assertEqual(cliente.rut, "12345678-5")
        self.assertEqual(cliente.telefono, "+56912345678")

    def test_r9_correo_duplicado_rechazado_sin_importar_mayusculas(self):
        self._registrar_carolina("carolina@mail.cl")
        with self.assertRaises(ErrorNegocio):
            self._registrar_carolina("CAROLINA@mail.cl")

    def test_registro_con_contrasena_debil_rechazado(self):
        with self.assertRaises(ErrorValidacion):
            self.auth.registrar_cliente("Ana Soto", "12.345.678-5", "ana@mail.cl",
                                        "+56912345678", "abc")

    def test_registro_con_rut_invalido_rechazado_y_sin_eco_del_rut(self):
        try:
            self.auth.registrar_cliente("Ana Soto", "12.345.678-9", "ana@mail.cl",
                                        "+56912345678", PASSWORD)
            self.fail("Debió rechazar el RUT")
        except ErrorValidacion as error:
            self.assertNotIn("12345678", str(error).replace(".", ""))

    def test_no_se_puede_crear_un_usuario_abstracto(self):
        with self.assertRaises(TypeError):
            Usuario("Ana", "ana@mail.cl", "hash")

    # ---- RF02: login -----------------------------------------------------------
    def test_login_correcto_devuelve_el_usuario(self):
        self._registrar_carolina()
        usuario = self.auth.iniciar_sesion("  CAROLINA@mail.cl ", PASSWORD)
        self.assertEqual(usuario.correo, "carolina@mail.cl")

    def test_login_con_contrasena_incorrecta_falla(self):
        self._registrar_carolina()
        with self.assertRaises(ErrorAutenticacion):
            self.auth.iniciar_sesion("carolina@mail.cl", "Otra-Clave9")

    def test_mensaje_identico_si_el_correo_no_existe_o_la_clave_es_mala(self):
        self._registrar_carolina()
        mensajes = set()
        for correo in ("carolina@mail.cl", "noexiste@mail.cl", "esto-no-es-correo"):
            try:
                self.auth.iniciar_sesion(correo, "Otra-Clave9")
            except ErrorAutenticacion as error:
                mensajes.add(str(error))
        self.assertEqual(mensajes, {"Credenciales inválidas."})

    def test_rnf06_inyeccion_sql_en_el_login_no_da_acceso(self):
        self._registrar_carolina()
        for correo in ("' OR '1'='1", "x@x.cl' OR 1=1 --"):
            with self.assertRaises(ErrorAutenticacion):
                self.auth.iniciar_sesion(correo, "' OR '1'='1")

    def test_entradas_de_tipo_incorrecto_no_rompen_el_login(self):
        for correo, clave in ((None, None), (123, "x"), ("a@b.cl", None), ("", "")):
            with self.assertRaises(ErrorAutenticacion):
                self.auth.iniciar_sesion(correo, clave)

    # ---- bloqueo por fuerza bruta (S11) ------------------------------------------
    def test_s11_tras_5_fallos_se_bloquea_incluso_con_la_clave_correcta(self):
        self._registrar_carolina()
        for _ in range(5):
            with self.assertRaises(ErrorAutenticacion):
                self.auth.iniciar_sesion("carolina@mail.cl", "Otra-Clave9")
        with self.assertRaises(ErrorAutenticacion) as ctx:
            self.auth.iniciar_sesion("carolina@mail.cl", PASSWORD)
        self.assertIn("Demasiados intentos", str(ctx.exception))

    def test_s11_el_bloqueo_expira_con_el_tiempo(self):
        self._registrar_carolina()
        for _ in range(5):
            with self.assertRaises(ErrorAutenticacion):
                self.auth.iniciar_sesion("carolina@mail.cl", "Otra-Clave9")
        self.reloj.ahora += ServicioAutenticacion.SEGUNDOS_BLOQUEO + 1
        self.assertIsNotNone(self.auth.iniciar_sesion("carolina@mail.cl", PASSWORD))

    def test_un_login_exitoso_reinicia_el_contador_de_fallos(self):
        self._registrar_carolina()
        for _ in range(4):
            with self.assertRaises(ErrorAutenticacion):
                self.auth.iniciar_sesion("carolina@mail.cl", "Otra-Clave9")
        self.auth.iniciar_sesion("carolina@mail.cl", PASSWORD)
        for _ in range(4):      # otros 4 fallos NO deben bloquear (el contador volvió a 0)
            with self.assertRaises(ErrorAutenticacion) as ctx:
                self.auth.iniciar_sesion("carolina@mail.cl", "Otra-Clave9")
            self.assertNotIn("Demasiados", str(ctx.exception))

    # ---- roles y polimorfismo -----------------------------------------------------
    def test_s7_crear_administrador_y_su_login_devuelve_administrador(self):
        self.auth.crear_administrador("Ignacio Salas", "ignacio@agencia.cl", PASSWORD)
        usuario = self.auth.iniciar_sesion("ignacio@agencia.cl", PASSWORD)
        self.assertIsInstance(usuario, Administrador)
        self.assertEqual(usuario.rol, "ADMINISTRADOR")

    def test_polimorfismo_cada_rol_responde_distinto_al_mismo_mensaje(self):
        cliente = self._registrar_carolina()
        admin = self.auth.crear_administrador("Ignacio Salas", "ignacio@agencia.cl", PASSWORD)
        self.assertEqual(cliente.rol, "CLIENTE")
        self.assertEqual(admin.rol, "ADMINISTRADOR")
        self.assertNotEqual(cliente.resumen(), admin.resumen())

    def test_r17_resumen_y_repr_no_exponen_rut_telefono_ni_hash(self):
        cliente = self._registrar_carolina()
        for texto in (cliente.resumen(), repr(cliente)):
            self.assertNotIn("12345678", texto)
            self.assertNotIn("56912345678", texto)
            self.assertNotIn("$2", texto)

    def test_r17_enmascarado_oculta_la_mayor_parte(self):
        cliente = self._registrar_carolina()
        self.assertEqual(cliente.rut_enmascarado(), "******78-5")
        self.assertEqual(cliente.telefono_enmascarado(), "*********678")


if __name__ == "__main__":
    unittest.main()
