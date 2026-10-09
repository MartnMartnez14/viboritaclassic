import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location(
    "viborita", Path(__file__).resolve().parents[1] / "Untitled-1.py"
)
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)


class HistorialTests(unittest.TestCase):
    def setUp(self):
        self.juego = modulo.Vibora.__new__(modulo.Vibora)
        self.juego.historial = []
        self.juego.terminado = False
        self.juego.inicio_partida = 100
        self.juego.puntos = 4
        self.juego.lienzo = Mock()
        self.juego.raiz = Mock()
        self.juego.dibujar = Mock()
        self.juego.sesion_var = Mock()
        self.juego.resultados = Mock()
        self.juego.puntos_var = Mock()
        self.juego.paneles_efectos = {}
        self.juego.motivo_final = ""

    def test_finalizar_registra_una_sola_vez(self):
        with patch.object(modulo.time, "monotonic", return_value=255.9):
            self.juego.finalizar()
            self.juego.finalizar()
        self.assertEqual(len(self.juego.historial), 1)
        partida = self.juego.historial[0]
        self.assertEqual(partida["duracion"], 155)
        self.assertEqual(partida["niveles"], 4)
        self.assertRegex(partida["hora"], r"^\d{2}:\d{2}$")

    def test_reiniciar_conserva_historial_y_reinicia_reloj(self):
        registro = {"hora": "18:42", "duracion": 155, "niveles": 4}
        self.juego.historial.append(registro)
        with patch.object(modulo.time, "monotonic", return_value=300):
            self.juego.reiniciar()
        self.assertEqual(self.juego.historial, [registro])
        self.assertEqual(self.juego.puntos, 0)
        self.assertEqual(self.juego.inicio_partida, 300)
        self.assertFalse(self.juego.terminado)

    def test_historial_reciente_primero_y_total(self):
        self.juego.historial = [
            {"hora": "18:38", "duracion": 72, "niveles": 2},
            {"hora": "18:42", "duracion": 155, "niveles": 4},
        ]
        self.juego.actualizar_historial()
        self.juego.sesion_var.set.assert_called_with("2 partidas · 6 niveles acumulados")
        textos = [llamada.args[1] for llamada in self.juego.resultados.insert.call_args_list]
        self.assertIn("18:42 · Tiempo: 02:35", textos[0])
        self.assertIn("18:38 · Tiempo: 01:12", textos[1])

    def test_panel_no_tapa_tablero(self):
        self.juego.panel = Mock()
        self.juego.panel.winfo_reqwidth.return_value = 624
        self.juego.panel.winfo_reqheight.return_value = 560
        self.juego.fondo = Mock()
        self.juego.panel_id = 1
        self.juego.historial_id = 2
        self.juego.estrellas = []
        for ancho, alto, estado in [
            (760, 650, "hidden"),
            (1366, 768, "normal"),
            (1000, 1000, "normal"),
            (624, 564, "hidden"),
        ]:
            with self.subTest(ancho=ancho, alto=alto):
                self.juego.ajustar_cielo(SimpleNamespace(width=ancho, height=alto))
                opciones = self.juego.fondo.itemconfigure.call_args.kwargs
                self.assertEqual(opciones["state"], estado)


if __name__ == "__main__":
    unittest.main()
