from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from test_historial import modulo


class NuevosEfectosTests(unittest.TestCase):
    def setUp(self):
        self.juego = modulo.Vibora.__new__(modulo.Vibora)
        self.juego.raiz = Mock()
        self.juego.paneles_efectos = {}
        self.juego.puntos_var = Mock()
        self.juego.dibujar = Mock()
        self.juego.historial = []
        self.juego.actualizar_historial = Mock()
        self.juego.lienzo = Mock()
        self.juego.reiniciar()
        self.juego.vibora = [(3, 3), (2, 3), (1, 3)]
        self.juego.comidas = {}

    def consumir(self, efecto):
        x, y = self.juego.vibora[0]
        self.juego.comidas = {(x + 1, y): "#22c55e"}
        with patch.object(self.juego, "sortear_efecto", return_value=efecto) as sorteo:
            self.juego.avanzar()
        sorteo.assert_called_once()

    def test_experiencia_desde_siguiente_consumo(self):
        self.consumir("Experiencia aumentada")
        self.assertEqual(self.juego.puntos, 1)
        self.assertEqual(self.juego.experiencia_por_comida, 2)
        self.consumir("Experiencia aumentada")
        self.assertEqual(self.juego.puntos, 3)
        self.consumir("Experiencia reducida")
        self.assertEqual(self.juego.puntos, 6)
        self.assertEqual(self.juego.experiencia_por_comida, 2)
        self.assertEqual(self.juego.consumidas, 3)
        self.assertEqual(len(self.juego.vibora), 6)
        self.assertEqual(self.juego.velocidad, 133)
        self.juego.finalizar()
        self.assertEqual(self.juego.historial[0]["niveles"], 6)

    def test_minimos_y_acumulaciones_sin_deudas(self):
        for nombre in ("Ruptura de escudo", "Experiencia reducida", "Antimagnetismo"):
            self.juego.aplicar_efecto(nombre)
            self.assertIn("sin efecto", self.juego.registro_efectos[-1][1])
        for _ in range(3):
            for nombre in ("Escudo protector", "Experiencia aumentada", "Magnetismo"):
                self.juego.aplicar_efecto(nombre)
        self.assertEqual((self.juego.escudos, self.juego.experiencia_por_comida,
                          self.juego.radio_magnetismo), (3, 4, 3))
        for nombre in ("Ruptura de escudo", "Experiencia reducida", "Antimagnetismo"):
            self.juego.aplicar_efecto(nombre)
        self.assertEqual((self.juego.escudos, self.juego.experiencia_por_comida,
                          self.juego.radio_magnetismo), (2, 3, 2))
        self.assertEqual(self.juego.puntos, 0)

    def test_magnetismo_maximo(self):
        self.juego.radio_magnetismo = self.juego.COLUMNAS + self.juego.FILAS - 2
        self.juego.aplicar_efecto("Magnetismo")
        self.assertIn("sin efecto", self.juego.registro_efectos[-1][1])

    def test_escudo_pared_espera_y_reanuda(self):
        self.juego.vibora = [(23, 3), (22, 3), (21, 3)]
        self.juego.escudos = 3
        anterior = list(self.juego.vibora)
        self.juego.avanzar()
        self.assertEqual(self.juego.vibora, anterior)
        self.assertEqual(self.juego.escudos, 2)
        self.assertTrue(self.juego.esperando_salida)
        self.assertIsNone(self.juego.movimiento_id)
        self.juego.avanzar()
        self.juego.tecla_presionada(SimpleNamespace(keysym="Right"))
        self.juego.tecla_presionada(SimpleNamespace(keysym="Left"))
        self.assertEqual(self.juego.escudos, 2)
        self.assertTrue(self.juego.esperando_salida)
        self.juego.raiz.after.reset_mock()
        self.juego.tecla_presionada(SimpleNamespace(keysym="Up"))
        self.assertFalse(self.juego.esperando_salida)
        self.juego.raiz.after.assert_called_once()
        self.juego.avanzar()
        self.assertEqual(self.juego.vibora[0], (23, 2))

    def test_escudo_cuerpo_no_consume_otros_estados(self):
        self.juego.vibora = [(3, 3), (3, 4), (4, 4), (4, 3), (5, 3)]
        self.juego.escudos = 1
        self.juego.radio_magnetismo = 1
        self.juego.comidas = {(4, 2): "#22c55e"}
        self.juego.cargas_escurridizas = 1
        self.juego.crecimiento_pendiente = 1
        anterior = dict(self.juego.comidas)
        self.juego.avanzar()
        self.assertTrue(self.juego.esperando_salida)
        self.assertEqual(self.juego.escudos, 0)
        self.assertEqual(self.juego.comidas, anterior)
        self.assertEqual(self.juego.cargas_escurridizas, 1)
        self.assertEqual(self.juego.crecimiento_pendiente, 1)
        self.assertEqual(self.juego.consumidas, 0)

    def test_escudo_sin_salida_finaliza(self):
        self.juego.vibora = [(0, 0), (0, 1), (1, 1), (1, 0), (2, 0)]
        self.juego.direccion = self.juego.siguiente_direccion = "Up"
        self.juego.escudos = 2
        self.juego.avanzar()
        self.assertTrue(self.juego.terminado)
        self.assertEqual(self.juego.escudos, 1)
        self.assertIn("Sin dirección", self.juego.motivo_final)

    def test_choque_sin_escudo_finaliza(self):
        self.juego.vibora = [(23, 3), (22, 3), (21, 3)]
        self.juego.avanzar()
        self.assertTrue(self.juego.terminado)

    def test_magnetismo_contacto_distancia_y_desempate(self):
        self.juego.radio_magnetismo = 1
        self.juego.comidas = {(4, 4): "a", (4, 2): "b", (5, 3): "c"}
        self.assertEqual(self.juego.evaluar_movimiento("Right")[1], (4, 2))
        self.juego.comidas[(4, 3)] = "d"
        self.assertEqual(self.juego.evaluar_movimiento("Right")[1], (4, 3))
        self.juego.comidas = {(5, 4): "a"}
        self.assertIsNone(self.juego.evaluar_movimiento("Right")[1])
        self.juego.radio_magnetismo = 2
        self.assertEqual(self.juego.evaluar_movimiento("Right")[1], (5, 4))

    def test_magnetismo_una_pildora_por_movimiento(self):
        self.juego.radio_magnetismo = 1
        self.juego.comidas = {(4, 2): "a", (4, 4): "b"}
        with patch.object(self.juego, "sortear_efecto", return_value="Escudo protector") as sorteo:
            self.juego.avanzar()
        sorteo.assert_called_once()
        self.assertEqual(self.juego.consumidas, 1)
        self.assertEqual(len(self.juego.vibora), 4)
        self.assertIn((4, 4), self.juego.comidas)

    def test_magnetismo_escape_sin_recogida_alternativa(self):
        self.juego.radio_magnetismo = 2
        self.juego.cargas_escurridizas = 1
        self.juego.comidas = {(4, 2): "a", (4, 4): "b"}
        with patch.object(modulo.random, "choice", return_value=(5, 3)):
            with patch.object(self.juego, "sortear_efecto") as sorteo:
                self.juego.avanzar()
        sorteo.assert_not_called()
        self.assertEqual(self.juego.consumidas, 0)
        self.assertEqual(len(self.juego.vibora), 3)
        self.assertEqual(self.juego.comidas, {(5, 3): "a", (4, 4): "b"})

    def test_magnetismo_y_conservacion_cola(self):
        self.juego.vibora = [(2, 2), (2, 3), (1, 3), (1, 2)]
        self.juego.radio_magnetismo = 1
        self.juego.comidas = {(0, 2): "a"}
        self.assertTrue(self.juego.evaluar_movimiento("Left")[4])
        self.juego.cargas_escurridizas = 1
        self.assertFalse(self.juego.evaluar_movimiento("Left")[4])
        self.juego.crecimiento_pendiente = 1
        self.assertTrue(self.juego.evaluar_movimiento("Left")[4])

    def test_reinicio_cancela_temporizador_y_borra_estados(self):
        temporizador = self.juego.movimiento_id
        self.juego.escudos = 4
        self.juego.radio_magnetismo = 3
        self.juego.experiencia_por_comida = 5
        self.juego.esperando_salida = True
        self.juego.historial = [{"niveles": 7}]
        self.juego.reiniciar()
        self.juego.raiz.after_cancel.assert_called_with(temporizador)
        self.assertEqual((self.juego.escudos, self.juego.radio_magnetismo,
                          self.juego.experiencia_por_comida), (0, 0, 1))
        self.assertFalse(self.juego.esperando_salida)
        self.assertEqual(self.juego.historial, [{"niveles": 7}])

    def test_cada_movimiento_conserva_un_temporizador_cancelable(self):
        self.juego.raiz.after.side_effect = ["movimiento-1", "movimiento-2"]
        self.juego.avanzar()
        self.assertEqual(self.juego.movimiento_id, "movimiento-1")
        self.juego.avanzar()
        self.juego.raiz.after_cancel.assert_called_with("movimiento-1")
        self.assertEqual(self.juego.movimiento_id, "movimiento-2")


if __name__ == "__main__":
    unittest.main()
