import time
import unittest
from unittest.mock import Mock, patch

from test_historial import modulo

Serpiente = modulo.Serpiente


class LegendariosBase(unittest.TestCase):
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
        self.juego.vibora = [(10, 10), (9, 10), (8, 10)]
        self.juego.comidas = {}
        self.juego.serpientes = []

    def mover(self, plan):
        """Ejecuta un tick de invocadas con un plan fijo: lista de (serpiente, nombre, celda)."""
        previa = list(self.juego.vibora)
        with patch.object(self.juego, "planear_movimientos", return_value=plan):
            self.juego.mover_invocadas(previa)


class EventosLegendariosTests(LegendariosBase):
    def test_nivel_10_y_20_acumulan_sin_duplicar(self):
        self.juego.puntos = 10
        with patch.object(modulo.random, "random", return_value=0.1):
            self.juego.procesar_legendarios()
        self.assertEqual(self.juego.invocaciones_pendientes, ["guardiana"])
        self.juego.procesar_invocaciones()
        self.assertEqual(len(self.juego.serpientes), 1)

        self.juego.puntos = 20
        with patch.object(modulo.random, "random", return_value=0.9):
            self.juego.procesar_legendarios()
        self.juego.procesar_invocaciones()
        self.assertEqual(len(self.juego.serpientes), 2)
        self.assertEqual(self.juego.serpientes[1].tipo, "depredadora")

        self.juego.procesar_legendarios()
        self.juego.procesar_invocaciones()
        self.assertEqual(len(self.juego.serpientes), 2)
        self.assertEqual(self.juego.hitos_legendarios, 2)

    def test_salto_de_varios_niveles_procesa_cada_hito_una_vez(self):
        self.juego.puntos = 35
        with patch.object(modulo.random, "random", return_value=0.1):
            self.juego.procesar_legendarios()
        self.assertEqual(len(self.juego.invocaciones_pendientes), 3)
        self.juego.procesar_legendarios()
        self.assertEqual(len(self.juego.invocaciones_pendientes), 3)

    def test_probabilidad_configurable(self):
        self.juego.puntos = 10
        with patch.dict(modulo.Vibora.DIMENSIONES[0], {"prob_buff": 0.0}), \
                patch.object(modulo.random, "random", return_value=0.0):
            self.juego.procesar_legendarios()
        self.assertEqual(self.juego.invocaciones_pendientes, ["depredadora"])

    def test_invocacion_nunca_sobre_jugadora(self):
        for _ in range(60):
            self.juego.serpientes = []
            self.assertTrue(self.juego.invocar("depredadora"))
            cabeza = self.juego.vibora[0]
            for segmento in self.juego.serpientes[0].segmentos:
                self.assertNotIn(segmento, self.juego.vibora)
                distancia = max(abs(segmento[0] - cabeza[0]), abs(segmento[1] - cabeza[1]))
                self.assertGreater(distancia, 0)
            self.assertGreater(
                max(abs(self.juego.serpientes[0].cabeza[0] - cabeza[0]),
                    abs(self.juego.serpientes[0].cabeza[1] - cabeza[1])),
                self.juego.DISTANCIA_SEGURA_INVOCACION)

    def test_tablero_lleno_deja_invocacion_pendiente(self):
        self.juego.invocaciones_pendientes = ["guardiana"]
        with patch.object(self.juego, "celdas_cuerpos",
                          return_value={(x, y) for x in range(24) for y in range(20)}):
            self.juego.procesar_invocaciones()
        self.assertEqual(self.juego.invocaciones_pendientes, ["guardiana"])
        self.assertEqual(self.juego.serpientes, [])

    def test_limite_de_invocadas(self):
        self.juego.invocaciones_pendientes = ["guardiana"] * 3
        with patch.object(modulo.Vibora, "MAX_INVOCADAS", 2):
            self.juego.procesar_invocaciones()
        self.assertEqual(len(self.juego.serpientes), 2)
        self.assertEqual(len(self.juego.invocaciones_pendientes), 1)


class GuardianasTests(LegendariosBase):
    def test_guardiana_come_suma_un_punto_sin_sorteo_y_crece(self):
        guardiana = Serpiente("guardiana", [(2, 2), (1, 2), (0, 2)], "Right")
        self.juego.serpientes = [guardiana]
        self.juego.comidas = {(3, 2): "#ffffff"}
        with patch.object(self.juego, "sortear_efecto") as sorteo:
            self.mover([(guardiana, "Right", (3, 2))])
        sorteo.assert_not_called()
        self.assertEqual(len(guardiana.segmentos), 4)
        self.assertNotIn((3, 2), self.juego.comidas)
        self.assertEqual(self.juego.puntos, 1)
        self.assertEqual(self.juego.consumidas, 0)

    def test_guardiana_come_a_depredadora(self):
        guardiana = Serpiente("guardiana", [(2, 2), (1, 2), (0, 2)], "Right")
        enemiga = Serpiente("depredadora", [(3, 2), (4, 2), (5, 2)], "Right")
        self.juego.serpientes = [guardiana, enemiga]
        self.mover([(guardiana, "Right", (3, 2)), (enemiga, "Right", (6, 2))])
        self.assertEqual(len(enemiga.segmentos), 2)
        self.assertTrue(guardiana.segmentos)

    def test_guardiana_es_inmortal_y_no_dania(self):
        guardiana = Serpiente("guardiana", [(11, 10)], "Left")
        self.juego.serpientes = [guardiana]
        self.mover([(guardiana, "Left", (10, 10))])
        self.assertFalse(self.juego.terminado)
        self.assertEqual(len(self.juego.vibora), 3)
        self.assertEqual(len(self.juego.serpientes), 1)

    def test_guardiana_evita_cuerpo_de_jugadora(self):
        guardiana = Serpiente("guardiana", [(11, 10), (11, 9), (11, 8)], "Right")
        opciones = self.juego.opciones_invocada(guardiana, set(), set())
        self.assertNotIn("Left", [nombre for nombre, _ in opciones])
        self.assertTrue(all(celda not in self.juego.vibora for _, celda in opciones))


class CombateTests(LegendariosBase):
    def test_enemiga_no_dana_a_jugadora(self):
        # La depredadora ya no puede comer a la jugadora: la atraviesa sin daño.
        enemiga = Serpiente("depredadora", [(8, 9), (8, 8), (8, 7)], "Down")
        self.juego.serpientes = [enemiga]
        self.mover([(enemiga, "Down", (8, 10))])
        self.assertEqual(len(self.juego.vibora), 3)
        self.assertEqual(self.juego.invulnerable, 0)
        self.assertFalse(self.juego.terminado)

    def test_escudo_no_se_gasta_con_enemigas(self):
        enemiga = Serpiente("depredadora", [(8, 9), (8, 8), (8, 7)], "Down")
        self.juego.serpientes = [enemiga]
        self.juego.escudos = 1
        self.mover([(enemiga, "Down", (8, 10))])
        self.assertEqual(len(self.juego.vibora), 3)
        self.assertEqual(self.juego.escudos, 1)

    def test_jugadora_ataca_por_costado_sin_recibir_dano(self):
        self.juego.vibora = [(13, 10), (12, 11), (11, 11)]
        enemiga = Serpiente("depredadora", [(15, 10), (14, 10), (13, 10)], "Right")
        self.juego.serpientes = [enemiga]
        self.mover([(enemiga, "Up", (15, 9))])
        self.assertEqual(len(enemiga.segmentos), 2)
        self.assertEqual(len(self.juego.vibora), 3)
        self.assertEqual(self.juego.puntos, self.juego.PREMIO_GOLPE)
        self.assertEqual(enemiga.tamano_combate, 3)

    def test_choque_frontal_solo_resta_a_enemiga(self):
        enemiga = Serpiente("depredadora", [(10, 9), (10, 8), (10, 7)], "Down")
        self.juego.serpientes = [enemiga]
        self.mover([(enemiga, "Down", (10, 10))])
        self.assertEqual(len(enemiga.segmentos), 2)
        self.assertEqual(len(self.juego.vibora), 3)
        self.assertEqual(self.juego.puntos, self.juego.PREMIO_GOLPE)

    def test_enemiga_de_un_segmento_destruida_y_premiada(self):
        enemiga = Serpiente("depredadora", [(10, 9)], "Down")
        self.juego.serpientes = [enemiga]
        self.mover([(enemiga, "Down", (10, 10))])
        self.assertEqual(self.juego.serpientes, [])
        self.assertEqual(self.juego.derrotadas, 1)
        self.assertEqual(self.juego.puntos, self.juego.PREMIO_GOLPE)

    def test_jugadora_con_un_segmento_sobrevive_al_contacto(self):
        self.juego.vibora = [(10, 10)]
        enemiga = Serpiente("depredadora", [(10, 9), (10, 8), (10, 7)], "Down")
        self.juego.serpientes = [enemiga]
        self.juego.invulnerable = 0
        self.mover([(enemiga, "Down", (10, 10))])
        self.assertFalse(self.juego.terminado)
        self.assertEqual(len(self.juego.vibora), 1)
        self.assertEqual(len(enemiga.segmentos), 2)

    def test_varias_enemigas_no_danan_en_el_tick(self):
        enemiga_a = Serpiente("depredadora", [(8, 9), (8, 8), (8, 7)], "Down")
        enemiga_b = Serpiente("depredadora", [(9, 9), (9, 8), (9, 7)], "Down")
        self.juego.serpientes = [enemiga_a, enemiga_b]
        self.mover([(enemiga_a, "Down", (8, 10)), (enemiga_b, "Down", (9, 10))])
        self.assertEqual(len(self.juego.vibora), 3)
        self.assertFalse(self.juego.terminado)

    def test_depredadora_devora_guardiana_de_un_roce(self):
        guardiana = Serpiente("guardiana", [(5, 5), (5, 6), (5, 7)], "Up")
        enemiga = Serpiente("depredadora", [(5, 3), (5, 2), (5, 1)], "Down")
        self.juego.serpientes = [guardiana, enemiga]
        self.mover([(guardiana, "Up", (5, 4)), (enemiga, "Down", (5, 5))])
        self.assertNotIn(guardiana, self.juego.serpientes)
        self.assertEqual(self.juego.derrotadas, 0)
        self.assertTrue(any("devoró" in mensaje
                            for _, mensaje in self.juego.registro_efectos))

    def test_pildora_no_se_consume_dos_veces(self):
        guardiana = Serpiente("guardiana", [(2, 2), (1, 2), (0, 2)], "Right")
        enemiga = Serpiente("depredadora", [(4, 2), (5, 2), (6, 2)], "Left")
        self.juego.serpientes = [guardiana, enemiga]
        self.juego.comidas = {(3, 2): "#ffffff"}
        self.mover([(guardiana, "Right", (3, 2)), (enemiga, "Left", (3, 2))])
        self.assertNotIn((3, 2), self.juego.comidas)
        self.assertEqual(len(guardiana.segmentos), 4)
        self.assertEqual(len(enemiga.segmentos), 3)


class ReinicioYRendimientoTests(LegendariosBase):
    def test_reiniciar_limpia_invocaciones_contadores_y_eventos(self):
        self.juego.puntos = 25
        with patch.object(modulo.random, "random", return_value=0.1):
            self.juego.procesar_legendarios()
        self.juego.procesar_invocaciones()
        self.juego.derrotadas = 4
        self.juego.reiniciar()
        self.assertEqual(self.juego.serpientes, [])
        self.assertEqual(self.juego.invocaciones_pendientes, [])
        self.assertEqual(self.juego.hitos_legendarios, 0)
        self.assertEqual(self.juego.derrotadas, 0)
        self.assertIsNone(self.juego.aviso)

    def test_rendimiento_con_muchas_entidades(self):
        for _ in range(modulo.Vibora.MAX_INVOCADAS):
            self.juego.invocar("guardiana")
        inicio = time.monotonic()
        for _ in range(300):
            if self.juego.terminado:
                break
            self.mover_sin_jugadora()
        self.assertLess(time.monotonic() - inicio, 3.0)

    def mover_sin_jugadora(self):
        previa = list(self.juego.vibora)
        planes = self.juego.planear_movimientos(self.juego.vibora[0])
        with patch.object(self.juego, "planear_movimientos", return_value=planes):
            self.juego.mover_invocadas(previa)


class RegresionSombrasTests(LegendariosBase):
    def tick_real(self):
        previa = list(self.juego.vibora)
        self.juego.mover_invocadas(previa)

    def test_guardiana_arrinconada_rebota_con_marcha_atras(self):
        self.juego.vibora = [(20, 15), (19, 15), (18, 15)]
        guardiana = Serpiente("guardiana", [(0, 0), (1, 0), (2, 0)], "Up")
        self.juego.serpientes = [guardiana]
        quieta = 0
        for _ in range(10):
            previa = guardiana.cabeza
            self.tick_real()
            if guardiana.cabeza == previa:
                quieta += 1
        self.assertEqual(quieta, 0)

    def test_sombra_en_esquina_no_queda_parada(self):
        # U en la esquina: su única salida es la celda de su propia cola.
        self.juego.vibora = [(20, 15), (19, 15), (18, 15)]
        depredadora = Serpiente("depredadora", [(0, 0), (0, 1), (1, 1), (1, 0)], "Up")
        self.juego.serpientes = [depredadora]
        cabeza_previa = depredadora.cabeza
        for _ in range(3):
            self.tick_real()
        self.assertNotEqual(depredadora.cabeza, cabeza_previa)
        self.assertEqual(len(depredadora.segmentos), 4)
        self.assertEqual(len(set(depredadora.segmentos)), 4)

    def test_sombra_sin_plan_recibe_golpe_lateral(self):
        depredadora = Serpiente("depredadora", [(5, 5), (5, 6), (5, 7)], "Up")
        self.juego.serpientes = [depredadora]
        self.juego.vibora = [(5, 6), (6, 6), (7, 6)]
        self.mover_con_plan([])
        self.assertEqual(len(depredadora.segmentos), 2)
        self.assertEqual(self.juego.puntos, self.juego.PREMIO_GOLPE)

    def mover_con_plan(self, plan):
        previa = list(self.juego.vibora)
        with patch.object(self.juego, "planear_movimientos", return_value=plan):
            self.juego.mover_invocadas(previa)

    def test_guardiana_totalmente_bloqueada_usa_paso_espectral(self):
        # Cabeza en esquina, cuello y cola bloqueando todo (ni la reversa sirve).
        self.juego.vibora = [(20, 15), (19, 15), (18, 15)]
        guardiana = Serpiente("guardiana", [(0, 0), (1, 0), (0, 1), (1, 1)], "Up")
        self.juego.serpientes = [guardiana]
        self.tick_real()
        self.assertTrue(self.juego.dentro(guardiana.cabeza))
        # Sin duplicados: el paso espectral colapsa el solape.
        self.assertEqual(len(set(guardiana.segmentos)), len(guardiana.segmentos))

    def test_invocar_asigna_color_aleatorio_a_enemiga(self):
        colores = set()
        for _ in range(30):
            self.juego.serpientes = []
            self.assertTrue(self.juego.invocar("depredadora"))
            colores.add(self.juego.serpientes[0].color)
        self.assertTrue(colores <= set(modulo.Vibora.COLORES_DEPREDADORA))
        self.assertGreater(len(colores), 1)

    def test_guardiana_se_dibuja_solo_con_contorno(self):
        guardiana = Serpiente("guardiana", [(5, 5), (5, 6)], "Up")
        self.juego.serpientes = [guardiana]
        self.juego.lienzo = Mock()
        self.juego.dibujar_invocadas()
        self.assertTrue(self.juego.lienzo.create_rectangle.called)
        for llamada in self.juego.lienzo.create_rectangle.call_args_list:
            self.assertNotIn("fill", llamada.kwargs)

    def test_depredadora_persigue_sin_danar_con_planificacion_real(self):
        self.juego.vibora = [(8, 10), (9, 10), (10, 10)]
        depredadora = Serpiente("depredadora", [(8, 9), (8, 8), (8, 7)], "Down")
        self.juego.serpientes = [depredadora]
        with patch.object(modulo.random, "random", return_value=0.5):
            self.tick_real()
        self.assertEqual(len(depredadora.segmentos), 2)
        self.assertEqual(len(self.juego.vibora), 3)
        self.assertFalse(self.juego.terminado)


class PausaTests(LegendariosBase):
    def tecla(self, keysym):
        from types import SimpleNamespace
        self.juego.tecla_presionada(SimpleNamespace(keysym=keysym))

    def test_enter_pausa_y_espacio_reanuda(self):
        self.assertFalse(self.juego.pausado)
        self.tecla("Return")
        self.assertTrue(self.juego.pausado)
        self.assertIsNone(self.juego.movimiento_id)
        self.assertIn("pausa", self.juego.puntos_var.set.call_args[0][0].lower())
        self.tecla("space")
        self.assertFalse(self.juego.pausado)
        self.juego.raiz.after.assert_called()

    def test_en_pausa_no_avanza_ni_cambia_direccion(self):
        self.tecla("Return")
        vibora = list(self.juego.vibora)
        self.juego.avanzar()
        self.assertEqual(self.juego.vibora, vibora)
        self.tecla("Up")
        self.assertEqual(self.juego.siguiente_direccion, "Right")
        self.tecla("space")
        self.assertEqual(self.juego.siguiente_direccion, "Right")

    def test_reiniciar_quita_la_pausa(self):
        self.tecla("Return")
        self.assertTrue(self.juego.pausado)
        self.juego.reiniciar()
        self.assertFalse(self.juego.pausado)


class DimensionesTests(LegendariosBase):
    def test_instantanea_guarda_y_restaura(self):
        self.juego.vibora = [(5, 5), (4, 5), (3, 5)]
        self.juego.comidas = {(7, 7): "#fff"}
        self.juego.guardar_dimension()
        self.juego.vibora = [(1, 1)]
        self.juego.comidas = {}
        self.juego.cargar_dimension(0)
        self.assertEqual(self.juego.vibora, [(5, 5), (4, 5), (3, 5)])
        self.assertEqual(self.juego.comidas, {(7, 7): "#fff"})

    def test_dimension_nueva_empieza_fresca(self):
        self.juego.cargar_dimension(3)
        self.assertEqual(self.juego.dimension, 3)
        self.assertEqual(len(self.juego.vibora), 3)
        self.assertEqual(self.juego.velocidad, modulo.Vibora.DIMENSIONES[3]["velocidad"])
        self.assertEqual(self.juego.cantidad_comidas,
                         modulo.Vibora.DIMENSIONES[3]["comidas"])

    def test_portal_inactivo_antes_del_nivel_25(self):
        self.juego.puntos = 24
        self.assertFalse(self.juego.portal_activo)
        self.juego.puntos = 25
        self.assertTrue(self.juego.portal_activo)

    def test_portal_reaparece_cada_25_niveles(self):
        self.juego.puntos = 67
        self.juego.viajar()
        self.assertEqual(self.juego.umbral_portal, 75)
        self.assertFalse(self.juego.portal_activo)
        self.juego.puntos = 74
        self.assertFalse(self.juego.portal_activo)
        self.juego.puntos = 75
        self.assertTrue(self.juego.portal_activo)

    def test_viajar_en_hito_exact_avanza_al_siguiente(self):
        self.juego.puntos = 25
        self.juego.viajar()
        self.assertEqual(self.juego.umbral_portal, 50)
        self.assertFalse(self.juego.portal_activo)

    def test_entrar_al_portal_viaja_y_congela(self):
        self.juego.puntos = 50
        self.juego.vibora = [(11, 10), (10, 10), (9, 10)]
        self.juego.siguiente_direccion = "Right"
        self.juego.direccion = "Right"
        self.juego.comidas = {}
        self.juego.avanzar()
        self.assertEqual(self.juego.dimension, 1)
        self.assertEqual(len(self.juego.dimensiones[0]["vibora"]), 3)
        self.assertEqual(self.juego.dimensiones[0]["vibora"][0], self.juego.portal_pos)

    def test_viaje_es_ciclico_y_vuelve_al_primero(self):
        self.juego.puntos = 50
        self.juego.cargar_dimension(9)
        self.juego.vibora = [(11, 10), (10, 10), (9, 10)]
        self.juego.siguiente_direccion = "Right"
        self.juego.direccion = "Right"
        self.juego.comidas = {}
        self.juego.avanzar()
        self.assertEqual(self.juego.dimension, 0)

    def test_anti_rebote_tras_viajar(self):
        self.juego.puntos = 50
        self.juego.viajar()
        self.assertGreater(self.juego.enfriamiento_portal, 0)
        # La víbora nueva nace sobre el portal pero no viaja de inmediato.
        self.assertEqual(self.juego.vibora[0], self.juego.portal_pos)
        self.juego.avanzar()
        self.assertEqual(self.juego.dimension, 1)

    def test_portal_no_recibe_pildoras(self):
        self.juego.puntos = 50
        for _ in range(30):
            self.juego.reponer_comidas()
            self.assertNotIn(self.juego.portal_pos, self.juego.comidas)
            self.juego.comidas = {}

    def test_envolvente_atraviesa_bordes(self):
        self.juego.cargar_dimension(1)
        self.juego.vibora = [(23, 5), (22, 5), (21, 5)]
        self.juego.direccion = "Right"
        self.juego.siguiente_direccion = "Right"
        self.juego.comidas = {}
        self.juego.avanzar()
        self.assertFalse(self.juego.terminado)
        self.assertEqual(self.juego.vibora[0], (0, 5))

    def test_espejo_mueve_normal(self):
        from types import SimpleNamespace
        self.juego.cargar_dimension(7)
        self.juego.direccion = "Up"
        self.juego.siguiente_direccion = "Up"
        self.juego.tecla_presionada(SimpleNamespace(keysym="Left"))
        self.assertEqual(self.juego.siguiente_direccion, "Left")

    def test_espejo_muestra_pildora_reflejada_pero_se_come_en_real(self):
        import types
        self.juego.cargar_dimension(7)
        self.juego.comidas = {(6, 5): "#fff"}
        self.juego.lienzo = Mock()
        self.juego.dibujar = types.MethodType(modulo.Vibora.dibujar, self.juego)
        self.juego.dibujar()
        espejo_x = self.juego.COLUMNAS - 1 - 6
        dibujadas = [c.args for c in self.juego.lienzo.create_rectangle.call_args_list
                     if c.kwargs.get("fill") == "#fff"]
        self.assertIn((espejo_x * 25 + 4, 5 * 25 + 4, (espejo_x + 1) * 25 - 4, 6 * 25 - 4),
                      dibujadas)
        # Y se come en la celda real, no en la reflejada.
        self.juego.vibora = [(5, 5), (4, 5), (3, 5)]
        self.juego.direccion = "Right"
        self.juego.siguiente_direccion = "Right"
        self.juego.avanzar()
        self.assertNotIn((6, 5), self.juego.comidas)

    def test_puro_sin_efectos(self):
        self.juego.cargar_dimension(9)
        self.juego.vibora = [(5, 5), (4, 5), (3, 5)]
        self.juego.direccion = "Right"
        self.juego.siguiente_direccion = "Right"
        self.juego.comidas = {(6, 5): "#fff"}
        with patch.object(self.juego, "sortear_efecto") as sorteo:
            self.juego.avanzar()
        sorteo.assert_not_called()
        self.assertEqual(self.juego.puntos, self.juego.experiencia_por_comida)

    def test_errante_mueve_pildoras(self):
        self.juego.cargar_dimension(6)
        self.juego.comidas = {(5, 5): "#fff"}
        self.juego.ticks_pildora = 4
        self.juego.vibora = [(20, 15), (21, 15), (22, 15)]
        self.juego.direccion = "Left"
        self.juego.siguiente_direccion = "Left"
        self.juego.avanzar()
        self.assertNotIn((5, 5), self.juego.comidas)

    def test_niebla_tapa_lejos(self):
        import types
        self.juego.cargar_dimension(8)
        self.juego.lienzo = Mock()
        self.juego.dibujar = types.MethodType(modulo.Vibora.dibujar, self.juego)
        self.juego.dibujar()
        tapadas = [c for c in self.juego.lienzo.create_rectangle.call_args_list
                   if c.kwargs.get("fill") == modulo.Vibora.DIMENSIONES[8]["fondo"]]
        self.assertTrue(tapadas)

    def test_reiniciar_limpia_dimensiones(self):
        self.juego.puntos = 50
        self.juego.viajar()
        self.juego.reiniciar()
        self.assertEqual(self.juego.dimension, 0)
        self.assertEqual(self.juego.dimensiones, [None] * 10)


class TeclasTests(LegendariosBase):
    def tecla(self, keysym):
        from types import SimpleNamespace
        self.juego.tecla_presionada(SimpleNamespace(keysym=keysym))

    def girar(self, keysym, desde, esperada):
        self.juego.direccion = desde
        self.juego.siguiente_direccion = desde
        self.tecla(keysym)
        self.assertEqual(self.juego.siguiente_direccion, esperada, keysym)

    def test_wasd_mueve(self):
        self.girar("a", "Up", "Left")
        self.girar("s", "Left", "Down")
        self.girar("d", "Down", "Right")
        self.girar("w", "Right", "Up")
        self.girar("W", "Right", "Up")

    def test_numerico_mueve(self):
        for keysym, desde, esperada in [("4", "Up", "Left"), ("8", "Left", "Up"),
                                        ("6", "Up", "Right"), ("2", "Left", "Down"),
                                        ("KP_4", "Up", "Left"), ("KP_8", "Left", "Up"),
                                        ("KP_6", "Up", "Right"), ("KP_2", "Left", "Down")]:
            self.girar(keysym, desde, esperada)

    def test_alternativas_respetan_no_reversa(self):
        self.juego.direccion = "Right"
        self.juego.siguiente_direccion = "Right"
        self.tecla("a")
        self.assertEqual(self.juego.siguiente_direccion, "Right")


class MagnetismoTests(LegendariosBase):
    def test_magnetismo_come_enemiga_a_distancia(self):
        self.juego.radio_magnetismo = 2
        enemiga = Serpiente("depredadora", [(12, 10), (13, 10), (14, 10)], "Right")
        self.juego.serpientes = [enemiga]
        self.juego.comidas = {}
        self.juego.avanzar()
        self.assertEqual(len(enemiga.segmentos), 2)
        self.assertEqual(self.juego.puntos, self.juego.PREMIO_GOLPE)

    def test_magnetismo_no_come_guardiana(self):
        self.juego.radio_magnetismo = 2
        guardiana = Serpiente("guardiana", [(12, 10), (13, 10)], "Right")
        self.juego.serpientes = [guardiana]
        self.juego.comidas = {}
        self.juego.avanzar()
        self.assertEqual(len(guardiana.segmentos), 2)

    def test_magnetismo_solo_una_captura_por_tick(self):
        self.juego.radio_magnetismo = 3
        enemiga = Serpiente("depredadora", [(12, 10), (13, 10), (14, 10)], "Right")
        self.juego.serpientes = [enemiga]
        self.juego.comidas = {(11, 10): "#fff"}
        puntos_antes = self.juego.puntos
        self.juego.avanzar()
        # Comió píldora: la enemiga queda intacta.
        self.assertEqual(len(enemiga.segmentos), 3)
        self.assertGreater(self.juego.puntos, puntos_antes)

    def test_magnetismo_avisa_radio_en_registro(self):
        self.juego.aplicar_efecto("Magnetismo")
        self.assertIn("radio: 1", self.juego.registro_efectos[-1][1])
        self.juego.aplicar_efecto("Antimagnetismo")
        self.assertIn("radio: 0", self.juego.registro_efectos[-1][1])


if __name__ == "__main__":
    unittest.main()
