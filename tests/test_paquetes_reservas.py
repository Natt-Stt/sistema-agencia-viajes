"""Pruebas de paquetes y reservas (RF08 a RF17)."""
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from src.agencia_viajes.database import crear_esquema, obtener_conexion
from src.agencia_viajes.errores import ErrorAgencia, ErrorAutorizacion, ErrorValidacion
from src.agencia_viajes.models.administrador import Administrador
from src.agencia_viajes.models.cliente import Cliente
from src.agencia_viajes.repositories.repositorio_destinos import RepositorioDestinos
from src.agencia_viajes.repositories.repositorio_paquetes import RepositorioPaquetes
from src.agencia_viajes.repositories.repositorio_reservas import RepositorioReservas
from src.agencia_viajes.repositories.repositorio_usuarios import RepositorioUsuarios
from src.agencia_viajes.seguridad import CifradorDatos
from src.agencia_viajes.services.servicio_destinos import ServicioDestinos
from src.agencia_viajes.services.servicio_paquetes import ServicioPaquetes
from src.agencia_viajes.services.servicio_reservas import ServicioReservas


class PruebasPaquetesYReservas(unittest.TestCase):
    def setUp(self):
        self.con = obtener_conexion(":memory:")
        crear_esquema(self.con)
        usuarios = RepositorioUsuarios(self.con, CifradorDatos(CifradorDatos.generar_clave()))
        self.admin = usuarios.guardar(Administrador("Ignacio Salas", "admin@agencia.cl", "hash"))
        self.cliente = usuarios.guardar(Cliente("Ana Soto", "12.345.678-5", "ana@mail.cl",
                                               "+56912345678", "hash"))
        self.repo_destinos = RepositorioDestinos(self.con)
        servicio_destinos = ServicioDestinos(self.repo_destinos)
        self.destinos = [
            servicio_destinos.registrar(self.admin, "Cajón del Maipo", "RM", 1, 45000),
            servicio_destinos.registrar(self.admin, "Isla Damas", "Coquimbo", 1, 38000),
            servicio_destinos.registrar(self.admin, "Conguillío", "Araucanía", 3, 185000),
        ]
        self.repo_paquetes = RepositorioPaquetes(self.con)
        self.repo_reservas = RepositorioReservas(self.con)
        self.reloj = lambda: date(2030, 1, 1)
        self.paquetes = ServicioPaquetes(self.repo_paquetes, self.repo_destinos,
                                         self.repo_reservas, reloj=self.reloj)
        self.reservas = ServicioReservas(self.repo_reservas, self.repo_paquetes,
                                         reloj=self.reloj)

    def tearDown(self):
        self.con.close()

    def test_conexion_streamlit_puede_usarse_en_otro_hilo(self):
        conexion = obtener_conexion(":memory:", check_same_thread=False)
        try:
            with ThreadPoolExecutor(max_workers=1) as ejecutor:
                resultado = ejecutor.submit(
                    lambda: conexion.execute("SELECT 1").fetchone()[0]
                ).result()
            self.assertEqual(resultado, 1)
        finally:
            conexion.close()

    def _crear_publicado(self, cupo=5, ids=None):
        paquete = self.paquetes.crear(
            self.admin, "Escapada", "2030-02-10", "2030-02-12", cupo,
            ids or [destino.id for destino in self.destinos[:2]], margen=0.2,
        )
        return self.paquetes.publicar(self.admin, paquete.id)

    def test_precio_calculado_y_congelado_al_publicar(self):
        paquete = self._crear_publicado()
        self.assertEqual(paquete.precio_por_persona, 99600)
        servicio_destinos = ServicioDestinos(self.repo_destinos)
        servicio_destinos.modificar(self.admin, self.destinos[0].id, costo_base=90000)
        self.assertEqual(self.repo_paquetes.buscar(paquete.id).precio_por_persona, 99600)

    def test_rechaza_cantidad_fechas_destinos_duplicados_y_no_disponibles(self):
        casos = (
            ("2030-02-10", "2030-02-12", 5, [self.destinos[0].id]),
            ("2030-02-10", "2030-02-12", 5, [d.id for d in self.destinos] * 2),
            ("2030-02-12", "2030-02-12", 5, [d.id for d in self.destinos[:2]]),
        )
        for salida, regreso, cupo, ids in casos:
            with self.assertRaises(ErrorAgencia):
                self.paquetes.crear(self.admin, "Invalido", salida, regreso, cupo, ids)
        ServicioDestinos(self.repo_destinos).retirar(self.admin, self.destinos[1].id)
        with self.assertRaises(ErrorAgencia):
            self.paquetes.crear(self.admin, "Invalido", "2030-02-10", "2030-02-12",
                                5, [self.destinos[0].id, self.destinos[1].id])

    def test_solo_admin_crea_y_publica_y_publicado_no_se_modifica(self):
        with self.assertRaises(ErrorAutorizacion):
            self.paquetes.crear(self.cliente, "X", "2030-02-10", "2030-02-12", 5,
                                [d.id for d in self.destinos[:2]])
        paquete = self._crear_publicado()
        with self.assertRaises(ErrorAgencia):
            self.paquetes.modificar_borrador(self.admin, paquete.id, nombre="Alterado")

    def test_reservar_calcula_total_y_actualiza_cupo(self):
        paquete = self._crear_publicado(cupo=4)
        reserva = self.reservas.reservar(self.cliente, paquete.id, 3)
        self.assertEqual(reserva.total, paquete.precio_por_persona * 3)
        self.assertEqual(self.paquetes.listar_publicados(self.cliente)[0][1], 1)

    def test_transaccion_rechaza_sobreventa_paquete_vencido_y_duplicado_activo(self):
        paquete = self._crear_publicado(cupo=3)
        self.reservas.reservar(self.cliente, paquete.id, 1)
        with self.assertRaises(ErrorAgencia):
            self.reservas.reservar(self.cliente, paquete.id, 1)
        segundo = RepositorioUsuarios(
            self.con, CifradorDatos(CifradorDatos.generar_clave())
        ).guardar(Cliente("Bea Soto", "10.000.013-K", "bea@mail.cl",
                          "+56987654321", "hash"))
        with self.assertRaises(ErrorAgencia):
            self.reservas.reservar(segundo, paquete.id, 3)
        vencido = self.paquetes.crear(self.admin, "Vencido", "2029-12-10", "2029-12-12", 5,
                                      [d.id for d in self.destinos[:2]])
        self.paquetes.publicar(self.admin, vencido.id)
        with self.assertRaises(ErrorAgencia):
            self.reservas.reservar(self.cliente, vencido.id, 1)

    def test_historial_aislado_cancelacion_libera_cupo_y_admin_confirma(self):
        paquete = self._crear_publicado(cupo=2)
        reserva = self.reservas.reservar(self.cliente, paquete.id, 2)
        cifrador = CifradorDatos(CifradorDatos.generar_clave())
        repositorio_usuarios = RepositorioUsuarios(self.con, cifrador)
        segundo = repositorio_usuarios.guardar(Cliente("Bea Soto", "10.000.013-K", "bea@mail.cl",
                                                        "+56987654321", "hash"))
        self.assertEqual(len(self.reservas.historial(segundo)), 0)
        with self.assertRaises(ErrorAgencia):
            self.reservas.cancelar(segundo, reserva.id)
        self.reservas.confirmar(self.admin, reserva.id)
        confirmada = self.reservas.historial(self.cliente)[0]
        self.assertEqual(confirmada.id_confirmado_por, self.admin.id)
        self.reservas.cancelar(self.cliente, reserva.id)
        nueva = self.reservas.reservar(segundo, paquete.id, 2)
        self.assertEqual(nueva.estado.value, "PENDIENTE")

    def test_no_acepta_cupo_margen_ni_personas_invalidos(self):
        for cupo, margen in ((0, 0.2), (3, -0.1)):
            with self.assertRaises(ErrorAgencia):
                self.paquetes.crear(self.admin, "Invalido", "2030-02-10", "2030-02-12",
                                    cupo, [d.id for d in self.destinos[:2]], margen=margen)
        paquete = self._crear_publicado()
        with self.assertRaises(ErrorValidacion):
            self.reservas.reservar(self.cliente, paquete.id, 0)


if __name__ == "__main__":
    unittest.main()