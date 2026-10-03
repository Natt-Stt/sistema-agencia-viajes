"""Pruebas del Sprint 1: destinos (RF03 a RF07, R1, R2, R7, R8, RNF06, RNF07).

Cada prueba usa una base de datos EN MEMORIA, nueva y vacía: no toca tu archivo
data/agencia.db y no depende del orden de ejecución.

Ejecutar desde la raíz:   python -m unittest discover -s tests -t . -v
"""
import unittest

from src.agencia_viajes.database import crear_esquema, obtener_conexion
from src.agencia_viajes.errores import ErrorAutorizacion, ErrorNegocio, ErrorValidacion
from src.agencia_viajes.models.administrador import Administrador
from src.agencia_viajes.models.cliente import Cliente
from src.agencia_viajes.repositories.repositorio_destinos import RepositorioDestinos
from src.agencia_viajes.services.servicio_destinos import (
    DESACTIVADO, ELIMINADO, ServicioDestinos)


class PruebasDestinos(unittest.TestCase):
    def setUp(self):
        self.con = obtener_conexion(":memory:")
        crear_esquema(self.con)
        self.repo = RepositorioDestinos(self.con)
        self.servicio = ServicioDestinos(self.repo)
        # Actores de prueba (no necesitan estar en la BD para probar permisos):
        self.admin = Administrador("Ignacio Salas", "ignacio@agencia.cl", "hash-falso")
        self.cliente = Cliente("Ana Soto", "12.345.678-5", "ana@mail.cl", "+56912345678", "hash-falso")

    def tearDown(self):
        self.con.close()

    # ---- utilidades de prueba ------------------------------------------------
    def _registrar_elqui(self):
        return self.servicio.registrar(self.admin, "Valle del Elqui", "Región de Coquimbo", 2, 120000)

    def _meter_en_paquete(self, id_destino, precio=100000):
        """Crea un paquete publicado que incluye el destino (SQL directo de prueba)."""
        with self.con:
            cur = self.con.execute(
                "INSERT INTO paquetes (nombre, fecha_salida, fecha_regreso, cupo_maximo,"
                " precio_por_persona, estado) VALUES ('Paquete X', '2027-01-10',"
                " '2027-01-15', 8, ?, 'PUBLICADO')", (precio,))
            id_paquete = cur.lastrowid
            self.con.execute(
                "INSERT INTO paquete_destino (id_paquete, id_destino) VALUES (?, ?)",
                (id_paquete, id_destino))
        return id_paquete

    # ---- RNF04 / RN08: solo el administrador gestiona destinos ---------------
    def test_rnf04_un_cliente_no_puede_gestionar_destinos(self):
        destino = self._registrar_elqui()
        acciones = (
            lambda: self.servicio.registrar(self.cliente, "X", "Z", 1, 1000),
            lambda: self.servicio.modificar(self.cliente, destino.id, costo_base=1),
            lambda: self.servicio.listar(self.cliente),
            lambda: self.servicio.retirar(self.cliente, destino.id),
        )
        for accion in acciones:
            with self.assertRaises(ErrorAutorizacion):
                accion()

    def test_rnf04_sin_sesion_tampoco_se_puede_gestionar_destinos(self):
        with self.assertRaises(ErrorAutorizacion):
            self.servicio.registrar(None, "X", "Z", 1, 1000)

    def test_rnf04_el_rechazo_no_modifica_los_datos(self):
        destino = self._registrar_elqui()
        with self.assertRaises(ErrorAutorizacion):
            self.servicio.retirar(self.cliente, destino.id)
        self.assertIsNotNone(self.repo.buscar(destino.id))

    # ---- RF03: registrar -----------------------------------------------------
    def test_registrar_destino_valido_asigna_id(self):
        destino = self._registrar_elqui()
        self.assertIsNotNone(destino.id)
        self.assertTrue(destino.disponible)
        self.assertEqual(self.repo.buscar(destino.id).nombre, "Valle del Elqui")

    def test_r1_nombre_duplicado_rechazado_sin_importar_mayusculas(self):
        self._registrar_elqui()
        with self.assertRaises(ErrorNegocio):
            self.servicio.registrar(self.admin, "VALLE DEL ELQUI", "Otra zona", 1, 50000)

    def test_r1_nombre_vacio_rechazado(self):
        with self.assertRaises(ErrorValidacion):
            self.servicio.registrar(self.admin, "   ", "Zona", 1, 50000)

    def test_r2_costo_cero_o_negativo_rechazado(self):
        for costo in (0, -5000):
            with self.assertRaises(ErrorValidacion):
                self.servicio.registrar(self.admin, f"Destino {costo}", "Zona", 1, costo)

    def test_r2_costo_no_entero_rechazado(self):
        for costo in (1000.5, "1000", None, True):
            with self.assertRaises(ErrorValidacion):
                self.servicio.registrar(self.admin, "Destino", "Zona", 1, costo)

    def test_duracion_cero_rechazada(self):
        with self.assertRaises(ErrorValidacion):
            self.servicio.registrar(self.admin, "Destino", "Zona", 0, 50000)

    # ---- RF04: modificar -----------------------------------------------------
    def test_modificar_cambia_solo_los_campos_indicados(self):
        destino = self._registrar_elqui()
        self.servicio.modificar(self.admin, destino.id, costo_base=130000)
        actualizado = self.repo.buscar(destino.id)
        self.assertEqual(actualizado.costo_base, 130000)
        self.assertEqual(actualizado.nombre, "Valle del Elqui")

    def test_modificar_destino_inexistente_falla(self):
        with self.assertRaises(ErrorNegocio):
            self.servicio.modificar(self.admin, 999, costo_base=1000)

    def test_modificar_a_nombre_ya_usado_falla(self):
        self._registrar_elqui()
        otro = self.servicio.registrar(self.admin, "Isla Damas", "Región de Coquimbo", 1, 38000)
        with self.assertRaises(ErrorNegocio):
            self.servicio.modificar(self.admin, otro.id, nombre="Valle del Elqui")

    def test_modificar_con_costo_invalido_no_altera_lo_guardado(self):
        destino = self._registrar_elqui()
        with self.assertRaises(ErrorValidacion):
            self.servicio.modificar(self.admin, destino.id, costo_base=0)
        self.assertEqual(self.repo.buscar(destino.id).costo_base, 120000)

    # ---- RF05: listar --------------------------------------------------------
    def test_listar_todos_y_solo_disponibles(self):
        elqui = self._registrar_elqui()
        self.servicio.registrar(self.admin, "Isla Damas", "Región de Coquimbo", 1, 38000)
        self._meter_en_paquete(elqui.id)
        self.servicio.retirar(self.admin, elqui.id)   # queda no disponible
        self.assertEqual(len(self.servicio.listar(self.admin)), 2)
        disponibles = self.servicio.listar(self.admin, solo_disponibles=True)
        self.assertEqual([d.nombre for d in disponibles], ["Isla Damas"])

    # ---- RF06 y RF07: retirar (R8) ------------------------------------------
    def test_r8_destino_sin_paquetes_se_elimina(self):
        destino = self._registrar_elqui()
        self.assertEqual(self.servicio.retirar(self.admin, destino.id), ELIMINADO)
        self.assertIsNone(self.repo.buscar(destino.id))

    def test_r8_destino_en_paquete_se_desactiva_y_no_se_elimina(self):
        destino = self._registrar_elqui()
        self._meter_en_paquete(destino.id)
        self.assertEqual(self.servicio.retirar(self.admin, destino.id), DESACTIVADO)
        guardado = self.repo.buscar(destino.id)
        self.assertIsNotNone(guardado)
        self.assertFalse(guardado.disponible)

    def test_r8_la_base_de_datos_tambien_impide_eliminar_destino_en_paquete(self):
        # Defensa en profundidad: aunque el servicio fallara, ON DELETE RESTRICT protege.
        destino = self._registrar_elqui()
        self._meter_en_paquete(destino.id)
        with self.assertRaises(ErrorNegocio):
            self.repo.eliminar(destino.id)

    # ---- R7: el precio de un paquete publicado no cambia ---------------------
    def test_r7_cambiar_costo_de_destino_no_altera_precio_del_paquete(self):
        destino = self._registrar_elqui()
        id_paquete = self._meter_en_paquete(destino.id, precio=144000)
        self.servicio.modificar(self.admin, destino.id, costo_base=999000)
        precio = self.con.execute(
            "SELECT precio_por_persona FROM paquetes WHERE id = ?", (id_paquete,)
        ).fetchone()[0]
        self.assertEqual(precio, 144000)

    # ---- RNF06: inyección SQL ------------------------------------------------
    def test_rnf06_texto_con_sql_se_guarda_como_texto_y_no_se_ejecuta(self):
        nombre_malicioso = "x'); DROP TABLE destinos; --"
        destino = self.servicio.registrar(self.admin, nombre_malicioso, "Zona", 1, 1000)
        self.assertEqual(self.repo.buscar(destino.id).nombre, nombre_malicioso)
        self.assertEqual(len(self.servicio.listar(self.admin)), 1)   # la tabla sigue existiendo

    # ---- RNF07: la BD rechaza datos inválidos aunque se salte el código ------
    def test_rnf07_check_de_la_bd_rechaza_costo_cero_por_sql_directo(self):
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute(
                "INSERT INTO destinos (nombre, zona, duracion_dias, costo_base)"
                " VALUES ('Malo', 'Z', 1, 0)")


if __name__ == "__main__":
    unittest.main()
