"""Pruebas de validaciones (RNF06, R9, R17)."""
import unittest

from src.agencia_viajes import validaciones as v
from src.agencia_viajes.errores import ErrorValidacion


class PruebasValidaciones(unittest.TestCase):
    # ---- RUT (módulo 11) ----
    def test_rut_valido_en_distintos_formatos_se_normaliza(self):
        for entrada in ("12.345.678-5", "12345678-5", "123456785", " 12.345.678-5 "):
            self.assertEqual(v.validar_rut(entrada), "12345678-5")

    def test_rut_con_cuerpo_de_menos_de_siete_cifras_es_valido(self):
        for entrada, esperado in (("1-9", "1-9"), ("123456-0", "123456-0")):
            with self.subTest(entrada=entrada):
                self.assertEqual(v.validar_rut(entrada), esperado)

    def test_rut_con_guion_tipografico_y_espacios_unicode_se_normaliza(self):
        entradas = (
            "12.345.678\u20135",
            "12\u00a0345\u202f678\u00a0-\u00a05",
            "12.345.678\u22125",
        )
        for entrada in entradas:
            with self.subTest(entrada=entrada):
                self.assertEqual(v.validar_rut(entrada), "12345678-5")

    def test_rut_con_k_valido(self):
        self.assertEqual(v.validar_rut("10.000.013-k"), "10000013-K")

    def test_rut_con_digito_verificador_incorrecto_rechazado(self):
        with self.assertRaises(ErrorValidacion):
            v.validar_rut("12.345.678-9")

    def test_rut_con_formato_invalido_rechazado(self):
        for entrada in ("", "abc", "12345678901-5", None, 12345678):
            with self.assertRaises(ErrorValidacion):
                v.validar_rut(entrada)

    def test_r17_mensaje_de_error_no_repite_el_rut(self):
        try:
            v.validar_rut("12.345.678-9")
        except ErrorValidacion as error:
            self.assertNotIn("12", str(error))
            self.assertNotIn("678", str(error))

    # ---- correo ----
    def test_correo_valido_se_normaliza_a_minusculas(self):
        self.assertEqual(v.validar_correo("  Ana.Perez@Mail.COM "), "ana.perez@mail.com")

    def test_correo_invalido_rechazado(self):
        for entrada in ("", "sin-arroba", "a@b", "a b@c.cl", "@c.cl", None):
            with self.assertRaises(ErrorValidacion):
                v.validar_correo(entrada)

    # ---- teléfono ----
    def test_telefono_se_normaliza(self):
        self.assertEqual(v.validar_telefono("+56 9 1234-5678"), "+56912345678")

    def test_telefono_invalido_rechazado_y_sin_eco(self):
        for entrada in ("abc", "123", "+56 9 12ab 5678", None):
            with self.assertRaises(ErrorValidacion):
                v.validar_telefono(entrada)
        try:
            v.validar_telefono("98765")
        except ErrorValidacion as error:
            self.assertNotIn("98765", str(error))

    # ---- contraseña ----
    def test_password_fuerte_aceptada(self):
        self.assertEqual(v.validar_password_fuerte("Clave-Segura1"), "Clave-Segura1")

    def test_password_debil_rechazada(self):
        for entrada in ("Ab1", "sinmayusculas1", "SINMINUSCULAS1", "SinNumeros", None):
            with self.assertRaises(ErrorValidacion):
                v.validar_password_fuerte(entrada)

    def test_password_de_mas_de_72_bytes_rechazada(self):
        with self.assertRaises(ErrorValidacion):
            v.validar_password_fuerte("Aa1" + "x" * 70)

    # ---- nombre ----
    def test_nombre_valido_con_tilde_y_ene(self):
        self.assertEqual(v.validar_nombre("  María   Ñancupil-O'Higgins "), "María Ñancupil-O'Higgins")

    def test_nombre_invalido_rechazado(self):
        for entrada in ("", "A", "123", "<script>", "Ana; DROP TABLE", None):
            with self.assertRaises(ErrorValidacion):
                v.validar_nombre(entrada)


if __name__ == "__main__":
    unittest.main()
