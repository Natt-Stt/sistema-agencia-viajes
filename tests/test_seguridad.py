"""Pruebas de hash (bcrypt) y cifrado (Fernet): R10, R17, RNF03, RNF05."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.agencia_viajes import seguridad
from src.agencia_viajes.errores import ErrorNegocio, ErrorValidacion


def setUpModule():
    seguridad.COSTO_BCRYPT = 4      # el mínimo de bcrypt: acelera las pruebas (producción usa 12)


class PruebasHash(unittest.TestCase):
    def test_r10_el_hash_no_contiene_la_contrasena(self):
        hash_ = seguridad.hashear_password("Clave-Segura1")
        self.assertNotIn("Clave-Segura1", hash_)
        self.assertTrue(hash_.startswith("$2"))      # formato bcrypt

    def test_verificar_correcta_e_incorrecta(self):
        hash_ = seguridad.hashear_password("Clave-Segura1")
        self.assertTrue(seguridad.verificar_password("Clave-Segura1", hash_))
        self.assertFalse(seguridad.verificar_password("clave-segura1", hash_))

    def test_misma_contrasena_produce_hashes_distintos_por_la_sal(self):
        self.assertNotEqual(seguridad.hashear_password("Clave-Segura1"),
                            seguridad.hashear_password("Clave-Segura1"))

    def test_hash_corrupto_o_vacio_no_rompe_y_devuelve_falso(self):
        for basura in ("", "no-es-un-hash", "$2b$04$corto"):
            self.assertFalse(seguridad.verificar_password("Clave-Segura1", basura))

    def test_contrasena_de_mas_de_72_bytes_rechazada(self):
        with self.assertRaises(ErrorValidacion):
            seguridad.hashear_password("A" * 73)


class PruebasCifrado(unittest.TestCase):
    def setUp(self):
        self.cifrador = seguridad.CifradorDatos(seguridad.CifradorDatos.generar_clave())

    def test_r17_cifrar_y_descifrar_devuelve_el_original(self):
        token = self.cifrador.cifrar("12345678-5")
        self.assertEqual(self.cifrador.descifrar(token), "12345678-5")

    def test_el_dato_cifrado_no_contiene_el_texto_original(self):
        token = self.cifrador.cifrar("12345678-5")
        self.assertNotIn("12345678", token)

    def test_clave_equivocada_no_puede_descifrar(self):
        token = self.cifrador.cifrar("12345678-5")
        otro = seguridad.CifradorDatos(seguridad.CifradorDatos.generar_clave())
        with self.assertRaises(ErrorNegocio):
            otro.descifrar(token)

    def test_dato_alterado_es_detectado(self):
        token = self.cifrador.cifrar("12345678-5")
        alterado = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
        with self.assertRaises(ErrorNegocio):
            self.cifrador.descifrar(alterado)

    def test_clave_invalida_rechazada(self):
        with self.assertRaises(ErrorNegocio):
            seguridad.CifradorDatos(b"esto-no-es-una-clave")


class PruebasCargaDeClave(unittest.TestCase):
    def test_se_crea_el_archivo_de_clave_la_primera_vez_y_se_reutiliza(self):
        with tempfile.TemporaryDirectory() as carpeta, \
                mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(seguridad.VARIABLE_CLAVE, None)
            ruta = Path(carpeta) / "clave.key"
            primero = seguridad.cargar_cifrador(ruta)
            self.assertTrue(ruta.exists())
            token = primero.cifrar("dato")
            segundo = seguridad.cargar_cifrador(ruta)      # lee la misma clave
            self.assertEqual(segundo.descifrar(token), "dato")

    def test_la_variable_de_entorno_tiene_prioridad(self):
        clave = seguridad.CifradorDatos.generar_clave().decode("ascii")
        with tempfile.TemporaryDirectory() as carpeta, \
                mock.patch.dict(os.environ, {seguridad.VARIABLE_CLAVE: clave}):
            ruta = Path(carpeta) / "clave.key"
            seguridad.cargar_cifrador(ruta)
            self.assertFalse(ruta.exists())                # no creó archivo


if __name__ == "__main__":
    unittest.main()
