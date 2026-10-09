import unittest
from unittest.mock import Mock, patch

from test_historial import modulo


class EfectosTests(unittest.TestCase):
    def setUp(self):
        self.juego = modulo.Vibora.__new__(modulo.Vibora)
        self.juego.raiz = Mock()
        self.juego.paneles_efectos = {}
        self.juego.puntos_var = Mock()
        self.juego.dibujar = Mock()
        self.juego.historial = [{"niveles": 3}]
        self.juego.reiniciar()

    def preparar_comida(self):
        self.juego.vibora = [(3, 3), (2, 3), (1, 3)]
        self.juego.comidas = {(4, 3): "#22c55e"}

    def test_sorteo_categorias_y_seis_opciones(self):
        for valor, categoria in [(0, "buff"), (0.4999, "buff"), (0.5, "debuff"), (0.99, "debuff")]:
            with patch.object(modulo.random, "random", return_value=valor):
                with patch.object(modulo.random, "choice", side_effect=lambda opciones: opciones[0]) as elegir:
                    nombre = self.juego.sortear_efecto()
                    self.assertEqual(self.juego.EFECTOS[nombre][0], categoria)
                    opciones = elegir.call_args.args[0]
                    self.assertEqual(len(opciones), 6)
                    self.assertTrue(all(self.juego.EFECTOS[n][0] == categoria for n in opciones))

    def test_multiplicidad_acumula_y_conserva_pildoras(self):
        original = dict(self.juego.comidas)
        for _ in range(2):
            self.juego.aplicar_efecto("Multiplicidad")
            self.juego.reponer_comidas()
        self.assertEqual(len(self.juego.comidas), 3)
        self.assertTrue(original.items() <= self.juego.comidas.items())
        self.assertFalse(set(self.juego.comidas) & set(self.juego.vibora))

    def test_consumo_repone_y_aplica_un_efecto(self):
        self.preparar_comida()
        with patch.object(self.juego, "sortear_efecto", return_value="Multiplicidad") as sorteo:
            self.juego.avanzar()
        self.assertEqual(self.juego.puntos, 1)
        self.assertEqual(len(self.juego.vibora), 4)
        self.assertEqual(len(self.juego.comidas), 2)
        sorteo.assert_called_once()

    def test_velocidad_y_limites(self):
        self.juego.velocidad = 100
        self.juego.aplicar_efecto("Ralentización")
        self.assertAlmostEqual(self.juego.velocidad, 100 / 0.9)
        self.juego.aplicar_efecto("Aceleración")
        self.assertAlmostEqual(self.juego.velocidad, 100 / 0.9 / 1.1)
        for _ in range(100):
            self.juego.aplicar_efecto("Aceleración")
        self.assertEqual(self.juego.velocidad, 25)
        for _ in range(100):
            self.juego.aplicar_efecto("Ralentización")
        self.assertEqual(self.juego.velocidad, 500)

    def test_escape_no_consume_ni_sortea(self):
        self.preparar_comida()
        self.juego.cargas_escurridizas = 2
        with patch.object(self.juego, "sortear_efecto") as sorteo:
            self.juego.avanzar()
        sorteo.assert_not_called()
        self.assertEqual(self.juego.puntos, 0)
        self.assertEqual(len(self.juego.vibora), 3)
        self.assertEqual(self.juego.vibora[0], (4, 3))
        self.assertNotIn((4, 3), self.juego.comidas)
        self.assertFalse(set(self.juego.comidas) & set(self.juego.vibora))
        self.assertEqual(self.juego.cargas_escurridizas, 1)

    def test_escape_sin_espacio_permite_comer(self):
        self.preparar_comida()
        self.juego.cargas_escurridizas = 1
        with patch.object(self.juego, "celdas_libres", return_value=[]):
            with patch.object(self.juego, "sortear_efecto", return_value="Multiplicidad"):
                self.juego.avanzar()
        self.assertEqual(self.juego.puntos, 1)
        self.assertEqual(self.juego.cargas_escurridizas, 0)
        self.assertEqual(self.juego.crecimiento_pendiente, 0)

    def test_reposicion_limitada_por_espacio(self):
        self.juego.COLUMNAS = 2
        self.juego.FILAS = 2
        self.juego.vibora = [(0, 0), (1, 0), (0, 1)]
        self.juego.comidas = {}
        self.juego.cantidad_comidas = 50
        self.juego.reponer_comidas()
        self.assertEqual(set(self.juego.comidas), {(1, 1)})

    def test_reinicio_borra_efectos_no_historial(self):
        self.juego.aplicar_efecto("Multiplicidad")
        self.juego.aplicar_efecto("Píldora escurridiza")
        self.juego.crecimiento_pendiente = 2
        self.juego.reiniciar()
        self.assertEqual(len(self.juego.historial), 1)
        self.assertEqual(len(self.juego.comidas), 1)
        self.assertEqual(self.juego.crecimiento_pendiente, 0)
        self.assertEqual(self.juego.cargas_escurridizas, 0)
        self.assertEqual(self.juego.registro_efectos, [])
        self.assertTrue(all(n == 0 for n in self.juego.conteo_efectos.values()))

    def test_paneles_fuera_del_tablero(self):
        self.juego.fondo = Mock()
        self.juego.paneles_efectos = {"buff": (1, Mock(), Mock()), "debuff": (2, Mock(), Mock())}
        self.juego.ajustar_paneles_efectos(1366, 768, 371)
        self.assertTrue(all(c.kwargs["state"] == "normal" for c in self.juego.fondo.itemconfigure.call_args_list))
        self.juego.fondo.itemconfigure.reset_mock()
        self.juego.ajustar_paneles_efectos(760, 650, 68)
        self.assertTrue(all(c.kwargs["state"] == "hidden" for c in self.juego.fondo.itemconfigure.call_args_list))

    def test_acortamiento_neto_y_colores(self):
        self.juego.vibora = [(6, 3), (5, 3), (4, 3), (3, 3), (2, 3)]
        self.juego.comidas = {(7, 3): "#22c55e"}
        with patch.object(self.juego, "sortear_efecto", return_value="Acortamiento"):
            self.juego.avanzar()
        self.assertEqual(len(self.juego.vibora), 4)
        self.assertEqual(self.juego.puntos, 1)
        self.assertEqual(len(self.juego.paleta_colores), 3)

    def test_acortamiento_inicial_sin_efecto(self):
        self.preparar_comida()
        with patch.object(self.juego, "sortear_efecto", return_value="Acortamiento") as sorteo:
            self.juego.avanzar()
        self.assertEqual(len(self.juego.vibora), 4)
        self.assertIn("sin efecto", self.juego.registro_efectos[-1][1])
        sorteo.assert_called_once()

    def test_acortamiento_respeta_minimo(self):
        self.juego.vibora = [(4, 3), (3, 3), (2, 3), (1, 3)]
        self.juego.comidas = {(5, 3): "#22c55e"}
        with patch.object(self.juego, "sortear_efecto", return_value="Acortamiento"):
            self.juego.avanzar()
        self.assertEqual(len(self.juego.vibora), self.juego.LONGITUD_INICIAL)

    def test_crecimiento_extra_inmediato(self):
        self.preparar_comida()
        with patch.object(self.juego, "sortear_efecto", return_value="Crecimiento extra"):
            self.juego.avanzar()
        self.assertEqual(len(self.juego.vibora), 5)
        self.assertEqual(len(set(self.juego.vibora)), 5)
        self.assertEqual(self.juego.puntos, 1)
        self.assertEqual(self.juego.crecimiento_pendiente, 0)
        self.assertEqual(len(self.juego.paleta_colores), 4)

    def test_crecimiento_diferido_cola_en_borde(self):
        self.preparar_comida()
        self.juego.vibora = [(2, 3), (1, 3), (0, 3)]
        self.juego.comidas = {(3, 3): "#22c55e"}
        with patch.object(self.juego, "sortear_efecto", return_value="Crecimiento extra"):
            self.juego.avanzar()
        self.assertEqual(len(self.juego.vibora), 4)
        self.assertEqual(self.juego.crecimiento_pendiente, 1)
        self.juego.comidas = {}
        self.juego.avanzar()
        self.assertEqual(len(self.juego.vibora), 5)
        self.assertEqual(self.juego.crecimiento_pendiente, 0)
        self.assertEqual(self.juego.puntos, 1)

    def test_extension_no_ocupa_comida_o_cuerpo(self):
        self.preparar_comida()
        self.juego.comidas[(0, 3)] = "#22c55e"
        self.assertFalse(self.juego.extender_cola())
        self.juego.comidas = {}
        self.juego.vibora = [(0, 3), (0, 2), (1, 2), (2, 2), (2, 3), (1, 3)]
        self.assertFalse(self.juego.extender_cola())

    def test_cola_con_carga_es_colision(self):
        self.juego.vibora = [(2, 2), (2, 3), (1, 3), (1, 2)]
        self.juego.siguiente_direccion = "Left"
        self.juego.comidas = {}
        self.juego.crecimiento_pendiente = 1
        self.juego.finalizar = Mock()
        self.juego.avanzar()
        self.juego.finalizar.assert_called_once()
        self.assertEqual(len(self.juego.vibora), 4)

    def test_cola_sin_carga_se_puede_ocupar(self):
        self.juego.vibora = [(2, 2), (2, 3), (1, 3), (1, 2)]
        self.juego.siguiente_direccion = "Left"
        self.juego.comidas = {}
        self.juego.finalizar = Mock()
        self.juego.avanzar()
        self.juego.finalizar.assert_not_called()
        self.assertEqual(len(set(self.juego.vibora)), 4)

    def test_escape_con_crecimiento_pendiente(self):
        self.preparar_comida()
        self.juego.crecimiento_pendiente = 1
        self.juego.cargas_escurridizas = 1
        with patch.object(self.juego, "sortear_efecto") as sorteo:
            self.juego.avanzar()
        sorteo.assert_not_called()
        self.assertEqual(len(self.juego.vibora), 4)
        self.assertEqual(self.juego.puntos, 0)
        self.assertEqual(self.juego.crecimiento_pendiente, 0)


if __name__ == "__main__":
    unittest.main()
