"""Juego clásico de la viborita, hecho con Tkinter."""

import copy
import math
import random
import tkinter as tk
import time
from datetime import datetime


class Serpiente:
    """Serpiente autónoma invocada por un evento legendario.

    tipo: "guardiana" (aliada, inmortal) o "depredadora" (enemiga).
    segmentos: lista de celdas; la primera es la cabeza.
    """

    def __init__(self, tipo, segmentos, direccion, color=None):
        self.tipo = tipo
        self.segmentos = list(segmentos)
        self.direccion = direccion
        self.tamano_combate = None
        self.color = color

    @property
    def aliada(self):
        return self.tipo == "guardiana"

    @property
    def cabeza(self):
        return self.segmentos[0]


class Vibora:
    """Controla el tablero, el movimiento y el estado de una partida."""

    # Configuración de eventos legendarios e invocaciones (ajustable).
    LEGENDARIO_CADA = 10
    PROB_LEGENDARIO_BUFF = 0.5
    MAX_INVOCADAS = 12
    LONGITUD_INVOCADA = 3
    DISTANCIA_SEGURA_INVOCACION = 2
    PROB_GUARDIANA_ALEATORIA = 0.7
    PROB_DEPREDADORA_ALEATORIA = 0.5
    PROB_DEPREDADORA_PERSECUCION = 0.35
    INVULNERABILIDAD_TICKS = 2
    PREMIO_GOLPE = 1
    COLOR_GUARDIANA = "#2dd4bf"
    COLORES_DEPREDADORA = ("#be123c", "#9333ea", "#e14389", "#ea580c", "#d97706")
    NIVEL_PORTAL = 25
    NUM_DIMENSIONES = 10
    # nombre, fondo nocturno, línea, velocidad inicial, píldoras, prob. buff, reglas.
    DIMENSIONES = (
        {"nombre": "Base", "fondo": "#101820", "linea": "#1e2d38", "velocidad": 145,
         "comidas": 1, "prob_buff": 0.5},
        {"nombre": "Envolvente", "fondo": "#0d1b2a", "linea": "#274264", "velocidad": 145,
         "comidas": 1, "prob_buff": 0.5, "envolvente": True, "pista": "los bordes conectan"},
        {"nombre": "Vértigo", "fondo": "#1c0f14", "linea": "#4c1d24", "velocidad": 90,
         "comidas": 1, "prob_buff": 0.5, "pista": "muy rápido"},
        {"nombre": "Sereno", "fondo": "#0b1a17", "linea": "#1d4a44", "velocidad": 200,
         "comidas": 3, "prob_buff": 0.5, "pista": "lento, 3 píldoras"},
        {"nombre": "Sombrío", "fondo": "#150f1e", "linea": "#3b2a5a", "velocidad": 145,
         "comidas": 1, "prob_buff": 0.25, "pista": "pocas guardianas"},
        {"nombre": "Luminoso", "fondo": "#0e1c22", "linea": "#2a5a6a", "velocidad": 145,
         "comidas": 1, "prob_buff": 0.75, "pista": "muchas guardianas"},
        {"nombre": "Errante", "fondo": "#1a1408", "linea": "#5a4a1d", "velocidad": 145,
         "comidas": 1, "prob_buff": 0.5, "moviles": True, "pista": "las píldoras se mueven"},
        {"nombre": "Espejo", "fondo": "#16121e", "linea": "#4a3a5a", "velocidad": 145,
         "comidas": 1, "prob_buff": 0.5, "pildoras_espejo": True,
         "pista": "las píldoras se ven reflejadas"},
        {"nombre": "Niebla", "fondo": "#05070d", "linea": "#1e2d38", "velocidad": 145,
         "comidas": 1, "prob_buff": 0.5, "niebla": True, "pista": "solo ves alrededor"},
        {"nombre": "Puro", "fondo": "#121212", "linea": "#3a3a3a", "velocidad": 145,
         "comidas": 1, "prob_buff": 0.5, "sin_efectos": True, "pista": "sin buffs ni debuffs"},
    )
    # Estado que congela cada dimensión (solo datos planos, sin widgets).
    CLAVES_DIMENSION = ("vibora", "direccion", "siguiente_direccion", "velocidad",
                        "paleta_colores", "comidas", "cantidad_comidas", "serpientes",
                        "invocaciones_pendientes", "esperando_salida",
                        "crecimiento_pendiente", "cargas_escurridizas")
    COLOR_FONDO_TABLERO = "#101820"

    TAM_CELDA = 25
    COLUMNAS = 24
    FILAS = 20
    LONGITUD_INICIAL = 3
    VELOCIDAD_INICIAL = 145
    INTERVALO_MINIMO = 25
    INTERVALO_MAXIMO = 500
    EFECTOS = {
        "Multiplicidad": ("buff", "+1 píldora disponible"),
        "Ralentización": ("buff", "-10% velocidad de movimiento"),
        "Acortamiento": ("buff", "-1 longitud neta si ya habías crecido"),
        "Escudo protector": ("buff", "+1 choque protegido"),
        "Experiencia aumentada": ("buff", "+1 experiencia en próximos consumos"),
        "Magnetismo": ("buff", "+1 radio de recogida"),
        "Aceleración": ("debuff", "+10% velocidad de movimiento"),
        "Píldora escurridiza": ("debuff", "+1 intento de comida que escapa"),
        "Crecimiento extra": ("debuff", "+1 segmento además del consumo"),
        "Ruptura de escudo": ("debuff", "-1 escudo, mínimo 0"),
        "Experiencia reducida": ("debuff", "-1 experiencia por consumo, mínimo 1"),
        "Antimagnetismo": ("debuff", "-1 radio, mínimo 0"),
    }
    PALETA_INICIAL = ("#22c55e", "#4ade80", "#16a34a")
    COLORES_PILDORA = (
        "#f43f5e",
        "#f97316",
        "#eab308",
        "#a855f7",
        "#ec4899",
        "#06b6d4",
        "#3b82f6",
        "#14b8a6",
        "#6366f1",
        "#84cc16",
    )

    DIRECCIONES = {
        "Up": (0, -1),
        "Down": (0, 1),
        "Left": (-1, 0),
        "Right": (1, 0),
    }
    # Teclas alternativas: WASD y teclado numérico (con o sin Bloq Num).
    TECLAS_ALT = {
        "w": "Up", "s": "Down", "a": "Left", "d": "Right",
        "8": "Up", "2": "Down", "4": "Left", "6": "Right",
        "kp_8": "Up", "kp_2": "Down", "kp_4": "Left", "kp_6": "Right",
        "kp_up": "Up", "kp_down": "Down", "kp_left": "Left", "kp_right": "Right",
    }
    OPUESTAS = {
        "Up": "Down",
        "Down": "Up",
        "Left": "Right",
        "Right": "Left",
    }

    def __init__(self, raiz):
        self.raiz = raiz
        self.raiz.title("Viborita clásica")
        self.raiz.resizable(True, True)
        self.raiz.configure(bg="#050711")
        self.raiz.geometry("760x650")
        self.raiz.minsize(624, 564)
        self.historial = []
        self.movimiento_id = None

        self.fondo = tk.Canvas(raiz, bg="#050711", highlightthickness=0)
        self.fondo.pack(fill="both", expand=True)
        self.panel = tk.Frame(self.fondo, bg="#050711")
        self.panel_id = self.fondo.create_window(0, 0, window=self.panel, anchor="center")
        self.estrellas = []
        generador = random.Random()
        for _ in range(180):
            radio = generador.choice((0.7, 0.9, 1.2, 1.6))
            brillo = generador.randint(80, 180)
            item = self.fondo.create_oval(0, 0, 0, 0, outline="")
            self.estrellas.append((
                item, generador.random(), generador.random(), radio, brillo,
                generador.uniform(0, math.tau), generador.uniform(0.3, 0.8),
                generador.random() < 0.3,
            ))
        self.fondo.tag_lower("all")
        self.fondo.tag_raise(self.panel_id)
        self.tiempo_cielo = 0
        self.animacion_cielo = None
        self.fondo.bind("<Configure>", self.ajustar_cielo)
        self.raiz.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.puntos_var = tk.StringVar()
        tk.Label(
            self.panel,
            textvariable=self.puntos_var,
            font=("Arial", 12, "bold"),
            bg="#050711",
            fg="#f8fafc",
            padx=12,
            pady=10,
            wraplength=600,
            justify="center",
        ).pack(fill="x")

        self.aviso_var = tk.StringVar(value="")
        self.aviso_label = tk.Label(
            self.panel,
            textvariable=self.aviso_var,
            font=("Arial", 11, "bold"),
            bg="#050711",
            fg="#f8fafc",
            padx=12,
            wraplength=600,
            justify="center",
        )
        self.aviso_label.pack(fill="x", pady=(0, 6))

        self.lienzo = tk.Canvas(
            self.panel,
            width=self.COLUMNAS * self.TAM_CELDA,
            height=self.FILAS * self.TAM_CELDA,
            bg="#101820",
            highlightthickness=0,
        )
        self.lienzo.pack(padx=12, pady=(0, 12))
        self.crear_panel_historial()
        self.crear_paneles_efectos()

        self.raiz.bind("<KeyPress>", self.tecla_presionada)
        self.reiniciar()
        self.animar_cielo()

    def ajustar_cielo(self, evento):
        """Adapta las estrellas y centra el juego al cambiar la ventana."""
        self.fondo.coords(self.panel_id, evento.width / 2, evento.height / 2)
        ancho_juego = self.panel.winfo_reqwidth()
        alto_juego = self.panel.winfo_reqheight()
        margen_izquierdo = (evento.width - ancho_juego) / 2
        margen_superior = (evento.height - alto_juego) / 2
        if margen_izquierdo >= 304:
            self.fondo.itemconfigure(self.historial_id, state="normal", height=min(360, evento.height - 32))
        elif margen_superior >= 180:
            self.fondo.itemconfigure(self.historial_id, state="normal", height=min(360, margen_superior - 32))
        else:
            self.fondo.itemconfigure(self.historial_id, state="hidden")
        self.ajustar_paneles_efectos(evento.width, evento.height, margen_izquierdo)
        for item, x, y, radio, *_ in self.estrellas:
            px, py = x * evento.width, y * evento.height
            self.fondo.coords(item, px - radio, py - radio, px + radio, py + radio)

    def crear_panel_historial(self):
        """Construye el panel de sesión, independiente del tablero."""
        marco = tk.Frame(self.fondo, bg="#0b1220", highlightbackground="#164e63",
                         highlightthickness=3)
        interior = tk.Frame(marco, bg="#0b1220", highlightbackground="#22d3ee",
                            highlightthickness=1)
        interior.pack(fill="both", expand=True, padx=2, pady=2)
        tk.Label(interior, text="PARTIDAS DE ESTA SESIÓN",
                 font=("Arial", 11, "bold"), fg="#67e8f9", bg="#0b1220",
                 pady=10).pack(fill="x")
        self.sesion_var = tk.StringVar(value="0 partidas · 0 niveles acumulados")
        tk.Label(interior, textvariable=self.sesion_var, font=("Arial", 9),
                 fg="#a5f3fc", bg="#0b1220").pack(fill="x", pady=(0, 8))
        lista = tk.Frame(interior, bg="#0b1220")
        lista.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        barra = tk.Scrollbar(lista, orient="vertical")
        barra.pack(side="right", fill="y")
        self.resultados = tk.Text(
            lista, bg="#0b1220", fg="#86efac", font=("Courier", 10),
            relief="flat", highlightthickness=0, wrap="word",
            state="disabled", cursor="arrow", yscrollcommand=barra.set,
            takefocus=False,
        )
        self.resultados.pack(side="left", fill="both", expand=True)
        barra.configure(command=self.resultados.yview)
        self.historial_id = self.fondo.create_window(
            16, 16, window=marco, anchor="nw", width=272, height=360,
            state="hidden",
        )
        self.actualizar_historial()

    def actualizar_historial(self):
        """Muestra primero los resultados más recientes, sin borrar la sesión."""
        total = sum(partida["niveles"] for partida in self.historial)
        self.sesion_var.set(f"{len(self.historial)} partidas · {total} niveles acumulados")
        self.resultados.configure(state="normal")
        self.resultados.delete("1.0", "end")
        if not self.historial:
            self.resultados.insert("end", "Todavía no hay partidas terminadas.")
        for partida in reversed(self.historial):
            minutos, segundos = divmod(partida["duracion"], 60)
            self.resultados.insert(
                "end",
                f'{partida["hora"]} · Tiempo: {minutos:02d}:{segundos:02d}\n'
                f'Niveles avanzados: {partida["niveles"]}\n\n',
            )
        self.resultados.configure(state="disabled")
        self.resultados.yview_moveto(0)

    def animar_cielo(self):
        """Hace titilar suavemente algunas estrellas en un único temporizador."""
        self.tiempo_cielo += 0.1
        for item, _, _, _, brillo, fase, ritmo, titila in self.estrellas:
            intensidad = brillo
            if titila:
                intensidad += int(35 * math.sin(self.tiempo_cielo * ritmo + fase))
            color = f"#{intensidad:02x}{min(255, intensidad + 8):02x}{min(255, intensidad + 25):02x}"
            self.fondo.itemconfigure(item, fill=color)
        self.animacion_cielo = self.raiz.after(100, self.animar_cielo)

    def crear_paneles_efectos(self):
        """Crea dos paneles neón con registros desplazables."""
        self.paneles_efectos = {}
        for categoria, titulo, fondo, color in (
            ("buff", "BUFFS", "#071b16", "#4ade80"),
            ("debuff", "DEBUFFS", "#210d18", "#fb7185"),
        ):
            marco = tk.Frame(self.fondo, bg=fondo, highlightbackground=color,
                             highlightthickness=2)
            tk.Label(marco, text=titulo, bg=fondo, fg=color,
                     font=("Arial", 12, "bold"), pady=8).pack(fill="x")
            resumen = tk.StringVar()
            tk.Label(marco, textvariable=resumen, bg=fondo, fg=color,
                     font=("Arial", 9), justify="left", wraplength=244).pack(fill="x", padx=8)
            lista = tk.Frame(marco, bg=fondo)
            lista.pack(fill="both", expand=True, padx=8, pady=8)
            barra = tk.Scrollbar(lista)
            barra.pack(side="right", fill="y")
            texto = tk.Text(lista, bg=fondo, fg=color, font=("Arial", 10),
                            wrap="word", relief="flat", highlightthickness=0,
                            takefocus=False, state="disabled",
                            yscrollcommand=barra.set)
            texto.pack(fill="both", expand=True)
            barra.configure(command=texto.yview)
            item = self.fondo.create_window(0, 0, window=marco, anchor="ne",
                                           width=272, height=300, state="hidden")
            self.paneles_efectos[categoria] = (item, resumen, texto)

    def ajustar_paneles_efectos(self, ancho, alto, margen):
        """Muestra ambos paneles solo cuando caben a la derecha del tablero."""
        altura = min(320, (alto - 48) // 2)
        visible = margen >= 304 and altura >= 180
        for indice, (item, _, _) in enumerate(self.paneles_efectos.values()):
            self.fondo.coords(item, ancho - 16, 16 + indice * (altura + 16))
            self.fondo.itemconfigure(item, height=altura,
                                     state="normal" if visible else "hidden")

    def actualizar_efectos(self):
        """Refleja acumulaciones y activaciones de la partida actual."""
        for categoria, (_, resumen, texto) in self.paneles_efectos.items():
            if categoria == "buff":
                estado = f"Píldoras: {len(self.comidas)} (objetivo: {self.cantidad_comidas})"
            else:
                estado = f"Trampas pendientes: {self.cargas_escurridizas}"
            resumen.set(f"{estado}\nMovimiento: {1000 / self.velocidad:.2f} celdas/s"
                        f" · {self.velocidad:.0f} ms\n"
                        f"Longitud: {len(self.vibora)} · Inicial: {self.LONGITUD_INICIAL}\n"
                        f"Crecimiento pendiente: {self.crecimiento_pendiente}\n"
                        f"Escudos: {self.escudos} · XP/píldora: {self.experiencia_por_comida}\n"
                        f"Radio magnético: {self.radio_magnetismo}")
            texto.configure(state="normal")
            texto.delete("1.0", "end")
            for nombre, (tipo, descripcion) in self.EFECTOS.items():
                if tipo == categoria:
                    texto.insert("end", f"{nombre} ×{self.conteo_efectos[nombre]}\n{descripcion}\n\n")
            texto.insert("end", "REGISTRO (recientes primero)\n")
            entradas = [mensaje for tipo, mensaje in self.registro_efectos if tipo == categoria]
            texto.insert("end", "\n".join(reversed(entradas)) or "Sin efectos adquiridos.")
            texto.configure(state="disabled")
            texto.yview_moveto(0)

    def cerrar(self):
        """Cancela los destellos antes de cerrar la ventana."""
        self.cancelar_movimiento()
        if self.animacion_cielo is not None:
            self.raiz.after_cancel(self.animacion_cielo)
        self.raiz.destroy()

    def reiniciar(self):
        """Devuelve todos los valores al comienzo de una partida."""
        self.cancelar_movimiento()
        centro_x = self.COLUMNAS // 2
        centro_y = self.FILAS // 2
        self.vibora = [
            (centro_x, centro_y),
            (centro_x - 1, centro_y),
            (centro_x - 2, centro_y),
        ]
        self.direccion = "Right"
        self.siguiente_direccion = "Right"
        self.puntos = 0
        self.consumidas = 0
        self.escudos = 0
        self.experiencia_por_comida = 1
        self.radio_magnetismo = 0
        self.esperando_salida = False
        self.motivo_final = ""
        self.inicio_partida = time.monotonic()
        self.velocidad = self.VELOCIDAD_INICIAL
        self.terminado = False
        self.paleta_colores = list(self.PALETA_INICIAL)
        self.comidas = {}
        self.cantidad_comidas = 1
        self.cargas_escurridizas = 0
        self.crecimiento_pendiente = 0
        self.conteo_efectos = dict.fromkeys(self.EFECTOS, 0)
        self.registro_efectos = []
        self.serpientes = []
        self.invocaciones_pendientes = []
        self.hitos_legendarios = 0
        self.derrotadas = 0
        self.invulnerable = 0
        self.pausado = False
        self.dimension = 0
        self.dimensiones = [None] * self.NUM_DIMENSIONES
        self.umbral_portal = self.NIVEL_PORTAL
        self.enfriamiento_portal = 0
        self.ticks_pildora = 0
        self.aviso = None
        if getattr(self, "aviso_var", None) is not None:
            self.aviso_var.set("")
        self.reponer_comidas()
        self.actualizar_efectos()
        self.actualizar_marcador()
        self.dibujar()
        self.programar_movimiento()

    def cancelar_movimiento(self):
        if getattr(self, "movimiento_id", None) is not None:
            self.raiz.after_cancel(self.movimiento_id)
            self.movimiento_id = None

    def programar_movimiento(self):
        self.cancelar_movimiento()
        if not self.terminado and not self.esperando_salida and not self.pausado:
            self.movimiento_id = self.raiz.after(round(self.velocidad), self.avanzar)

    def dim(self):
        """Reglas y paleta del tablero actual."""
        return self.DIMENSIONES[self.dimension]

    @property
    def portal_pos(self):
        return (self.COLUMNAS // 2, self.FILAS // 2)

    @property
    def portal_activo(self):
        return self.puntos >= self.umbral_portal and not self.terminado

    def guardar_dimension(self):
        """Congela el estado del tablero actual en memoria."""
        self.dimensiones[self.dimension] = {
            clave: copy.deepcopy(getattr(self, clave)) for clave in self.CLAVES_DIMENSION}

    def iniciar_dimension(self, indice):
        """Estado fresco para un tablero nunca visitado."""
        regla = self.DIMENSIONES[indice]
        centro_x = self.COLUMNAS // 2
        centro_y = self.FILAS // 2
        self.vibora = [(centro_x, centro_y), (centro_x - 1, centro_y), (centro_x - 2, centro_y)]
        self.direccion = "Right"
        self.siguiente_direccion = "Right"
        self.velocidad = regla["velocidad"]
        self.paleta_colores = list(self.PALETA_INICIAL)
        self.comidas = {}
        self.cantidad_comidas = regla["comidas"]
        self.serpientes = []
        self.invocaciones_pendientes = []
        self.esperando_salida = False
        self.crecimiento_pendiente = 0
        self.cargas_escurridizas = 0
        self.reponer_comidas()

    def cargar_dimension(self, indice):
        """Restaura el estado congelado o inicia el tablero si es nuevo."""
        instantanea = self.dimensiones[indice]
        self.dimension = indice
        if instantanea is None:
            self.iniciar_dimension(indice)
        else:
            for clave in self.CLAVES_DIMENSION:
                setattr(self, clave, copy.deepcopy(instantanea[clave]))
        self.lienzo.configure(bg=self.dim()["fondo"])

    def viajar(self):
        """Cruza el portal al siguiente tablero, en orden cíclico."""
        self.guardar_dimension()
        destino = (self.dimension + 1) % self.NUM_DIMENSIONES
        # El próximo portal aparece 50 niveles después del viaje actual.
        self.umbral_portal = (self.puntos // self.NIVEL_PORTAL + 1) * self.NIVEL_PORTAL
        self.cargar_dimension(destino)
        self.enfriamiento_portal = 3
        nombre = self.dim()["nombre"]
        self.registro_efectos.append(("buff", f"Portal al tablero {destino + 1}/10 ({nombre})."))
        if getattr(self, "aviso_var", None) is not None:
            self.aviso_var.set(f"Portal al tablero {destino + 1}/10: {nombre}.")
            self.aviso_label.configure(fg="#c4b5fd")
        self.aviso = ("Portal", f"Tablero {destino + 1}/10: {nombre}.",
                      "#c4b5fd", time.monotonic() + 2)
        self.actualizar_efectos()
        self.actualizar_marcador()
        self.dibujar()
        self.programar_movimiento()

    def evaluar_movimiento(self, direccion):
        """Calcula colisión y consumo sin alterar el estado ni sortear nada."""
        dx, dy = self.DIRECCIONES[direccion]
        x, y = self.vibora[0]
        cabeza = (x + dx, y + dy)
        if self.dim().get("envolvente"):
            # Los bordes conectan con el lado opuesto.
            cabeza = (cabeza[0] % self.COLUMNAS, cabeza[1] % self.FILAS)
        candidatos = [
            (abs(cx - cabeza[0]) + abs(cy - cabeza[1]), cx, cy)
            for cx, cy in self.comidas
            if abs(cx - cabeza[0]) + abs(cy - cabeza[1]) <= self.radio_magnetismo
        ]
        # Distancia, después columna y fila: desempate estable.
        objetivo = tuple(min(candidatos)[1:]) if candidatos else None
        destinos = []
        if objetivo is not None and self.cargas_escurridizas:
            destinos = [celda for celda in self.celdas_libres() if celda != cabeza]
        comera = objetivo is not None and not destinos
        cuerpo = self.vibora if comera or self.crecimiento_pendiente else self.vibora[:-1]
        colision = (not (0 <= cabeza[0] < self.COLUMNAS and 0 <= cabeza[1] < self.FILAS)
                    or cabeza in cuerpo)
        return cabeza, objetivo, destinos, comera, colision

    def direcciones_seguras(self):
        return [direccion for direccion in self.DIRECCIONES
                if direccion != self.OPUESTAS[self.direccion]
                and not self.evaluar_movimiento(direccion)[4]]

    def tecla_presionada(self, evento):
        """Cambia de dirección, pausa con Enter/Espacio o reinicia una partida terminada."""
        tecla = evento.keysym
        if self.terminado:
            if tecla.lower() == "r":
                self.reiniciar()
            return

        if tecla in ("Return", "KP_Enter", "space"):
            self.alternar_pausa()
            return
        if self.pausado:
            return

        tecla = self.TECLAS_ALT.get(tecla.lower(), tecla)
        if tecla in self.DIRECCIONES and tecla != self.OPUESTAS[self.direccion]:
            if self.esperando_salida:
                if tecla not in self.direcciones_seguras():
                    return
                self.esperando_salida = False
                self.siguiente_direccion = tecla
                self.actualizar_marcador()
                self.dibujar()
                self.programar_movimiento()
                return
            self.siguiente_direccion = tecla

    def alternar_pausa(self):
        """Pausa o reanuda la partida sin perder el estado."""
        if self.terminado:
            return
        self.pausado = not self.pausado
        if self.pausado:
            self.cancelar_movimiento()
        self.actualizar_marcador()
        self.dibujar()
        self.programar_movimiento()

    def avanzar(self):
        """Mueve una celda y programa el siguiente movimiento."""
        self.cancelar_movimiento()
        if self.terminado or self.esperando_salida or self.pausado:
            return

        if self.invulnerable:
            self.invulnerable -= 1
        if self.enfriamiento_portal:
            self.enfriamiento_portal -= 1
        self.direccion = self.siguiente_direccion
        nueva_cabeza, objetivo, destinos, comio, colision = self.evaluar_movimiento(self.direccion)
        intento_comida = objetivo is not None
        pendiente_anterior = self.crecimiento_pendiente
        longitud_anterior = len(self.vibora)

        if colision:
            if self.escudos:
                self.escudos -= 1
                self.registro_efectos.append(("buff", "Escudo usado: choque cancelado."))
                self.esperando_salida = True
                self.actualizar_efectos()
                if self.direcciones_seguras():
                    self.actualizar_marcador()
                    self.dibujar()
                    return
                self.motivo_final = "Sin dirección legal y segura."
            self.finalizar()
            return

        vibora_previa = list(self.vibora)
        self.vibora.insert(0, nueva_cabeza)
        if intento_comida and self.cargas_escurridizas:
            self.cargas_escurridizas -= 1
            if destinos:
                color = self.comidas.pop(objetivo)
                self.comidas[random.choice(destinos)] = color
                mensaje = "¡La píldora escapó! No se consumió."
            else:
                mensaje = "Sin espacio para escapar: trampa consumida."
            self.registro_efectos.append(("debuff", mensaje))
        if comio:
            self.puntos += self.experiencia_por_comida
            self.consumidas += 1
            self.velocidad = max(self.INTERVALO_MINIMO, self.velocidad - 4)
            self.paleta_colores.append(self.comidas.pop(objetivo))
            if pendiente_anterior and self.extender_cola():
                self.crecimiento_pendiente -= 1
                self.registro_efectos.append(("debuff", "Crecimiento pendiente aplicado."))
            if not self.dim().get("sin_efectos"):
                self.aplicar_efecto(self.sortear_efecto(), longitud_anterior)
            self.reponer_comidas()
            self.actualizar_marcador()
        elif pendiente_anterior:
            self.crecimiento_pendiente -= 1
            self.registro_efectos.append(("debuff", "Crecimiento pendiente aplicado."))
        else:
            self.vibora.pop()
        self.sincronizar_colores()
        if intento_comida or pendiente_anterior:
            self.actualizar_efectos()

        # Orden del tick: jugadora -> invocadas (movimiento, combate, comida)
        # -> reposición de píldoras -> eventos legendarios -> invocaciones pendientes.
        self.mover_invocadas(vibora_previa)
        if self.terminado:
            return
        if not comio:
            self.captura_magnetica()
        self.reponer_comidas()
        self.procesar_legendarios()
        self.procesar_invocaciones()
        if self.dim().get("moviles"):
            self.ticks_pildora += 1
            if self.ticks_pildora >= 5:
                self.ticks_pildora = 0
                self.mover_pildoras()
        if (self.portal_activo and not self.enfriamiento_portal
                and nueva_cabeza == self.portal_pos):
            self.viajar()
            return
        self.actualizar_marcador()
        self.actualizar_efectos()
        self.dibujar()
        if len(self.vibora) == self.COLUMNAS * self.FILAS:
            self.finalizar()
            return
        self.programar_movimiento()

    def celdas_cuerpos(self):
        """Celdas ocupadas por la jugadora y por todas las invocadas."""
        ocupadas = set(self.vibora)
        for serpiente in self.serpientes:
            ocupadas.update(serpiente.segmentos)
        return ocupadas

    def dentro(self, celda):
        return 0 <= celda[0] < self.COLUMNAS and 0 <= celda[1] < self.FILAS

    def pildora_mas_cercana(self, celda):
        if not self.comidas:
            return None
        return min(self.comidas, key=lambda p: abs(p[0] - celda[0]) + abs(p[1] - celda[1]))

    def opciones_invocada(self, serpiente, ocupadas, reservadas, permitir_reversa=False,
                            espectral=False):
        """Pasos válidos: sin invertir, dentro del tablero, sin chocar con cuerpos ni reservas.

        Las guardianas además evitan el cuerpo de la jugadora; las depredadoras no,
        porque pueden atacarla. Con permitir_reversa se acepta la marcha atrás
        como salida de emergencia contra la pared. Con espectral la guardiana
        atraviesa cuerpos (nunca paredes ni celdas reservadas) para no quedarse parada.
        """
        opuesta = self.OPUESTAS[serpiente.direccion]
        x, y = serpiente.cabeza
        # La cola propia se libera en este mismo tick, así que sí es un paso válido.
        cola_propia = serpiente.segmentos[-1]
        opciones = []
        for nombre, (dx, dy) in self.DIRECCIONES.items():
            if not permitir_reversa and len(serpiente.segmentos) > 1 and nombre == opuesta:
                continue
            celda = (x + dx, y + dy)
            if not self.dentro(celda) or celda in reservadas:
                continue
            if not espectral:
                if celda in ocupadas and celda != cola_propia:
                    continue
                if serpiente.aliada and celda in self.vibora:
                    continue
            opciones.append((nombre, celda))
        return opciones

    def elegir_paso(self, opciones, objetivo):
        if objetivo is None:
            return random.choice(opciones)
        # Empates: el orden aleatorio de opciones evita bucles deterministas.
        return min(opciones, key=lambda op: abs(op[1][0] - objetivo[0]) + abs(op[1][1] - objetivo[1]))

    def planear_movimientos(self, cabeza_jugador):
        """Decide el paso de cada invocada sin modificar el tablero."""
        ocupadas = self.celdas_cuerpos()
        # Las depredadoras pueden planear hacia el cuerpo de la jugadora (ataque).
        ocupadas_enemigas = ocupadas - set(self.vibora)
        reservadas = set()
        planes = []
        for serpiente in self.serpientes:
            bloqueadas = ocupadas if serpiente.aliada else ocupadas_enemigas
            opciones = self.opciones_invocada(serpiente, bloqueadas, reservadas)
            if not opciones:
                # Emergencia: marcha atrás aunque tenga varios segmentos.
                # Así la sombra rebota en la pared y sigue moviéndose infinito.
                opciones = self.opciones_invocada(serpiente, bloqueadas, reservadas,
                                                  permitir_reversa=True)
            if not opciones and serpiente.aliada:
                # Naturaleza espectral: la guardiana atraviesa cuerpos
                # (nunca paredes) antes que quedarse parada.
                opciones = self.opciones_invocada(serpiente, bloqueadas, reservadas,
                                                  permitir_reversa=True, espectral=True)
            if not opciones:
                continue
            random.shuffle(opciones)
            if serpiente.aliada:
                persigue_pildora = random.random() >= self.PROB_GUARDIANA_ALEATORIA
                objetivo = self.pildora_mas_cercana(serpiente.cabeza) if persigue_pildora else None
            else:
                r = random.random()
                if r < self.PROB_DEPREDADORA_ALEATORIA:
                    objetivo = None
                elif r < self.PROB_DEPREDADORA_ALEATORIA + self.PROB_DEPREDADORA_PERSECUCION:
                    objetivo = cabeza_jugador
                else:
                    objetivo = self.pildora_mas_cercana(serpiente.cabeza)
            nombre, celda = self.elegir_paso(opciones, objetivo)
            reservadas.add(celda)
            planes.append((serpiente, nombre, celda))
        return planes

    def registrar_golpe(self, serpiente, perdidas):
        """Marca un segmento perdido por la invocada en este tick."""
        if serpiente.tamano_combate is None:
            serpiente.tamano_combate = len(serpiente.segmentos)
        perdidas[id(serpiente)] = perdidas.get(id(serpiente), 0) + 1

    def captura_magnetica(self):
        """Con magnetismo, la jugadora come un segmento enemigo a distancia.

        Solo uno por tick, solo si no comió píldora (igual que el magnetismo
        normal) y nunca en su propia celda (eso ya lo resuelve el contacto).
        Las guardianas aliadas no se comen.
        """
        if not self.radio_magnetismo or self.terminado:
            return
        cabeza = self.vibora[0]
        candidatos = []
        for serpiente in self.serpientes:
            if serpiente.aliada:
                continue
            for segmento in serpiente.segmentos:
                distancia = abs(segmento[0] - cabeza[0]) + abs(segmento[1] - cabeza[1])
                if 0 < distancia <= self.radio_magnetismo:
                    candidatos.append((distancia, segmento[0], segmento[1], serpiente))
        if not candidatos:
            return
        candidatos.sort(key=lambda c: (c[0], c[1], c[2]))
        enemiga = candidatos[0][3]
        if enemiga.tamano_combate is None:
            enemiga.tamano_combate = len(enemiga.segmentos)
        if enemiga.segmentos:
            enemiga.segmentos.pop()
        self.puntos += self.PREMIO_GOLPE
        if not enemiga.segmentos:
            self.serpientes.remove(enemiga)
            self.derrotadas += 1
            self.registro_efectos.append(("buff", f"Nivel {self.puntos}: enemiga derrotada"))

    def recibir_dano_jugador(self, motivo):
        """Aplica un ataque enemigo: escudo, invulnerabilidad breve o pérdida de un segmento."""
        if self.invulnerable or self.terminado:
            return
        if self.escudos:
            self.escudos -= 1
            self.invulnerable = self.INVULNERABILIDAD_TICKS
            self.registro_efectos.append(("buff", f"Escudo absorbió un ataque ({motivo.lower()})."))
            return
        if len(self.vibora) <= 1:
            # El último segmento se queda visible al morir: nunca hay longitud cero en el tablero.
            self.motivo_final = "Una sombra depredadora te ha derribado."
            self.finalizar()
            return
        self.vibora.pop()
        self.invulnerable = self.INVULNERABILIDAD_TICKS
        self.sincronizar_colores()
        self.registro_efectos.append(("debuff", f"{motivo}: pierdes un segmento."))

    def mover_invocadas(self, vibora_previa):
        """Planea, resuelve combate y aplica los movimientos de todas las invocadas."""
        cabeza_jugador = self.vibora[0]
        planes = self.planear_movimientos(cabeza_jugador)
        perdidas = {}
        planes_por_id = {id(serpiente): (nombre, celda) for serpiente, nombre, celda in planes}
        # Depredadoras: ya no dañan a la jugadora. Solo la jugadora las come
        # (cabeza en su cuerpo: pierden un segmento) y ellas devoran guardianas.
        devoradas = set()
        cuerpos_guardianas = {id(s): (s, set(s.segmentos)) for s in self.serpientes if s.aliada}
        for serpiente in self.serpientes:
            if serpiente.aliada:
                continue
            antes = serpiente.segmentos
            plan = planes_por_id.get(id(serpiente))
            celda = plan[1] if plan else None
            contacto_jugador = (plan is not None and celda == cabeza_jugador) or (
                cabeza_jugador in antes)
            if contacto_jugador:
                # Choque o golpe por costado/cola: la enemiga pierde un segmento,
                # la jugadora no recibe daño.
                self.registrar_golpe(serpiente, perdidas)
                self.puntos += self.PREMIO_GOLPE
            if plan is not None:
                for gid, (_, cuerpo) in cuerpos_guardianas.items():
                    if celda in cuerpo:
                        # Un roce basta: la guardiana no sobrevive.
                        devoradas.add(gid)
                        break
            if self.terminado:
                return

        # Guardianas contra depredadoras: la cabeza guardiana que alcanza
        # un segmento enemigo le hace perder un segmento (probabilístico por su IA).
        cuerpos_enemigos = {}
        for serpiente in self.serpientes:
            if not serpiente.aliada:
                cuerpos_enemigos[id(serpiente)] = (serpiente, set(serpiente.segmentos))
        for serpiente in self.serpientes:
            if not serpiente.aliada:
                continue
            plan = planes_por_id.get(id(serpiente))
            if plan is None:
                continue
            celda = plan[1]
            for enemiga, cuerpo in cuerpos_enemigos.values():
                if celda in cuerpo:
                    self.registrar_golpe(enemiga, perdidas)
                    break

        for serpiente in self.serpientes:
            segmentos = list(serpiente.segmentos)
            plan = planes_por_id.get(id(serpiente))
            if plan:
                nombre, celda = plan
                comio = celda in self.comidas
                if comio:
                    del self.comidas[celda]
                    if serpiente.aliada:
                        self.puntos += 1
                segmentos.insert(0, celda)
                if not comio:
                    segmentos.pop()
                if celda in segmentos[1:]:
                    # Paso espectral sobre su propio cuerpo: colapsa el duplicado.
                    del segmentos[segmentos.index(celda, 1)]
                serpiente.direccion = nombre
            for _ in range(perdidas.get(id(serpiente), 0)):
                if segmentos:
                    segmentos.pop()
            serpiente.segmentos = segmentos

        supervivientes = []
        for serpiente in self.serpientes:
            if id(serpiente) in devoradas:
                self.registro_efectos.append(
                    ("debuff", "Una Sombra Depredadora devoró a tu Guardiana."))
                continue
            if serpiente.segmentos:
                supervivientes.append(serpiente)
                continue
            self.derrotadas += 1
            self.registro_efectos.append(("buff", f"Nivel {self.puntos}: enemiga derrotada"))
        self.serpientes = supervivientes

    def procesar_legendarios(self):
        """Procesa cada múltiplo de LEGENDARIO_CADA alcanzado, una sola vez por hito."""
        hitos = self.puntos // self.LEGENDARIO_CADA
        while self.hitos_legendarios < hitos:
            self.hitos_legendarios += 1
            nivel = self.hitos_legendarios * self.LEGENDARIO_CADA
            if random.random() < self.dim().get("prob_buff", self.PROB_LEGENDARIO_BUFF):
                tipo, categoria = "guardiana", "buff"
                aviso = ("¡INVOCACIÓN LEGENDARIA!", "Sombra Guardiana ha aparecido.", "#4ade80")
                nombre = "Sombra Guardiana"
            else:
                tipo, categoria = "depredadora", "debuff"
                aviso = ("¡MALDICIÓN LEGENDARIA!", "Una Sombra Depredadora acecha el tablero.", "#fb7185")
                nombre = "Sombra Depredadora"
            self.invocaciones_pendientes.append(tipo)
            self.registro_efectos.append((categoria, f"Nivel {nivel}: evento legendario ({nombre})"))
            self.aviso = (*aviso, time.monotonic() + 2)
            if getattr(self, "aviso_var", None) is not None:
                self.aviso_var.set(f"{aviso[0]} {aviso[1]}")
                self.aviso_label.configure(fg=aviso[2])

    def invocar(self, tipo):
        """Coloca una invocada con la cabeza lejos de la jugadora. Devuelve False si no hay hueco."""
        ocupadas = self.celdas_cuerpos() | set(self.comidas)
        cabeza_jugador = self.vibora[0]
        candidatas = [
            (x, y)
            for x in range(self.COLUMNAS)
            for y in range(self.FILAS)
            if (x, y) not in ocupadas
            and max(abs(x - cabeza_jugador[0]), abs(y - cabeza_jugador[1])) > self.DISTANCIA_SEGURA_INVOCACION
        ]
        random.shuffle(candidatas)
        direcciones = list(self.DIRECCIONES.items())
        for celda in candidatas:
            random.shuffle(direcciones)
            for nombre, (dx, dy) in direcciones:
                # La cabeza avanza en (dx, dy); el cuerpo queda detrás.
                cuerpo = [(celda[0] - k * dx, celda[1] - k * dy)
                          for k in range(self.LONGITUD_INVOCADA)]
                if all(self.dentro(c) and c not in ocupadas for c in cuerpo):
                    color = (None if tipo == "guardiana"
                             else random.choice(self.COLORES_DEPREDADORA))
                    self.serpientes.append(Serpiente(tipo, cuerpo, nombre, color=color))
                    return True
        return False

    def procesar_invocaciones(self):
        restantes = []
        for tipo in self.invocaciones_pendientes:
            if len(self.serpientes) >= self.MAX_INVOCADAS or not self.invocar(tipo):
                restantes.append(tipo)
        self.invocaciones_pendientes = restantes

    @staticmethod
    def mezclar(color, fondo, opacidad):
        """Simula transparencia mezclando el color con el fondo del tablero."""
        a = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(fondo[i:i + 2], 16) for i in (1, 3, 5)]
        return "#%02x%02x%02x" % tuple(round(opacidad * ca + (1 - opacidad) * cb)
                                       for ca, cb in zip(a, b))

    def celdas_libres(self):
        """Excluye todos los cuerpos, las píldoras y el portal activo."""
        ocupadas = self.celdas_cuerpos() | set(self.comidas)
        if self.portal_activo:
            ocupadas = ocupadas | {self.portal_pos}
        return [
            (x, y)
            for x in range(self.COLUMNAS)
            for y in range(self.FILAS)
            if (x, y) not in ocupadas
        ]

    def mover_pildoras(self):
        """Cada píldora da un paso a una celda vecina libre (tablero Errante)."""
        ocupadas = self.celdas_cuerpos() | {self.portal_pos}
        nuevas = {}
        for celda, color in list(self.comidas.items()):
            vecinas = [(celda[0] + dx, celda[1] + dy) for dx, dy in self.DIRECCIONES.values()]
            libres = [c for c in vecinas
                      if self.dentro(c) and c not in ocupadas and c not in nuevas]
            destino = random.choice(libres) if libres else celda
            nuevas[destino] = color
            ocupadas.add(destino)
        self.comidas = nuevas

    def reponer_comidas(self):
        libres = self.celdas_libres()
        cantidad = min(self.cantidad_comidas - len(self.comidas), len(libres))
        for celda in random.sample(libres, max(0, cantidad)):
            self.comidas[celda] = random.choice(self.COLORES_PILDORA)

    def sortear_efecto(self):
        categoria = "buff" if random.random() < 0.5 else "debuff"
        return random.choice([nombre for nombre, (tipo, _) in self.EFECTOS.items()
                              if tipo == categoria])

    def aplicar_efecto(self, nombre, longitud_anterior=None):
        detalle = ""
        if nombre == "Multiplicidad":
            self.cantidad_comidas += 1
        elif nombre == "Ralentización":
            self.velocidad /= 0.9
        elif nombre == "Aceleración":
            self.velocidad /= 1.1
        elif nombre == "Píldora escurridiza":
            self.cargas_escurridizas += 1
        elif nombre == "Acortamiento":
            anterior = len(self.vibora) - 1 if longitud_anterior is None else longitud_anterior
            if anterior > self.LONGITUD_INICIAL:
                del self.vibora[-2:]
                detalle = " (aplicado: -1 longitud neta)"
            else:
                detalle = " sin efecto: longitud mínima"
        elif nombre == "Crecimiento extra":
            if self.extender_cola():
                detalle = " (segmento añadido)"
            else:
                self.crecimiento_pendiente += 1
                detalle = " (crecimiento pendiente)"
        elif nombre == "Escudo protector":
            self.escudos += 1
        elif nombre == "Ruptura de escudo":
            if self.escudos:
                self.escudos -= 1
            else:
                detalle = " sin efecto: no hay cargas"
        elif nombre == "Experiencia aumentada":
            self.experiencia_por_comida += 1
        elif nombre == "Experiencia reducida":
            if self.experiencia_por_comida > 1:
                self.experiencia_por_comida -= 1
            else:
                detalle = " sin efecto: experiencia mínima"
        elif nombre == "Magnetismo":
            if self.radio_magnetismo < self.COLUMNAS + self.FILAS - 2:
                self.radio_magnetismo += 1
                detalle = f" (radio: {self.radio_magnetismo})"
            else:
                detalle = " sin efecto: alcance máximo"
        elif nombre == "Antimagnetismo":
            if self.radio_magnetismo:
                self.radio_magnetismo -= 1
                detalle = f" (radio: {self.radio_magnetismo})"
            else:
                detalle = " sin efecto: alcance básico"
        self.velocidad = min(self.INTERVALO_MAXIMO,
                             max(self.INTERVALO_MINIMO, self.velocidad))
        self.conteo_efectos[nombre] += 1
        categoria, _ = self.EFECTOS[nombre]
        self.registro_efectos.append((categoria, f"Nivel {self.puntos}: {nombre}{detalle}"))
        self.sincronizar_colores()

    def extender_cola(self):
        """Extiende siguiendo la cola si la celda siguiente es segura."""
        cola_x, cola_y = self.vibora[-1]
        anterior_x, anterior_y = self.vibora[-2]
        celda = (cola_x + cola_x - anterior_x, cola_y + cola_y - anterior_y)
        if (0 <= celda[0] < self.COLUMNAS and 0 <= celda[1] < self.FILAS
                and celda not in self.vibora and celda not in self.comidas):
            self.vibora.append(celda)
            return True
        return False

    def sincronizar_colores(self):
        """Conserva una paleta de longitud coherente con el cuerpo."""
        longitud = len(self.vibora) - 1
        while len(self.paleta_colores) < longitud:
            self.paleta_colores.append(self.paleta_colores[-1])
        del self.paleta_colores[longitud:]

    def actualizar_marcador(self):
        if self.pausado:
            self.puntos_var.set("En pausa: Enter o Espacio para seguir")
        elif self.esperando_salida:
            self.puntos_var.set("Escudo usado: elige una dirección segura con las flechas")
        else:
            aliadas = sum(1 for s in self.serpientes if s.aliada)
            enemigas = len(self.serpientes) - aliadas
            proximo = (self.hitos_legendarios + 1) * self.LEGENDARIO_CADA
            visitados = sum(1 for d in self.dimensiones if d is not None)
            portal = "listo" if self.portal_activo else f"nivel {self.umbral_portal}"
            pista = self.dim().get("pista")
            tablero = f"Tablero {self.dimension + 1}/10 ({self.dim()['nombre']})"
            if pista:
                tablero += f" · {pista}"
            self.puntos_var.set(
                f"Píldoras: {self.consumidas}   |   Niveles: {self.puntos}   |   Flechas para mover\n"
                f"{tablero}"
                f" · Visitados: {visitados} · Portal: {portal}"
                f"   |   Aliadas: {aliadas}   |   Enemigas: {enemigas}"
                f"   |   Derrotadas: {self.derrotadas}"
                f"   |   Próximo legendario: nivel {proximo}")

    def dibujar(self):
        """Redibuja el tablero para reflejar el estado actual."""
        regla = self.dim()
        fondo = regla["fondo"]
        self.lienzo.delete("all")
        for x in range(0, self.COLUMNAS * self.TAM_CELDA, self.TAM_CELDA):
            self.lienzo.create_line(x, 0, x, self.FILAS * self.TAM_CELDA, fill=regla["linea"])
        for y in range(0, self.FILAS * self.TAM_CELDA, self.TAM_CELDA):
            self.lienzo.create_line(0, y, self.COLUMNAS * self.TAM_CELDA, y, fill=regla["linea"])
        cabeza_x, cabeza_y = self.vibora[0]
        radio = self.radio_magnetismo
        if radio:
            for x in range(self.COLUMNAS):
                for y in range(self.FILAS):
                    distancia = abs(x - cabeza_x) + abs(y - cabeza_y)
                    if distancia <= radio and any(
                        abs(x + dx - cabeza_x) + abs(y + dy - cabeza_y) > radio
                        for dx, dy in self.DIRECCIONES.values()
                    ):
                        self.lienzo.create_rectangle(
                            x * self.TAM_CELDA + 1, y * self.TAM_CELDA + 1,
                            (x + 1) * self.TAM_CELDA - 1, (y + 1) * self.TAM_CELDA - 1,
                            outline="#155e75", dash=(2, 3),
                        )

        espejo = regla.get("pildoras_espejo")
        for celda, color in self.comidas.items():
            if espejo:
                # Engaño del espejo: se ve reflejada en horizontal, se come en su celda real.
                celda = (self.COLUMNAS - 1 - celda[0], celda[1])
            self.dibujar_celda(celda, color, margen=4)
        self.dibujar_invocadas()
        for indice, segmento in enumerate(self.vibora):
            color = "#dcfce7" if indice == 0 else self.paleta_colores[(indice - 1) % len(self.paleta_colores)]
            self.dibujar_celda(segmento, color, margen=2)
        if self.escudos:
            self.lienzo.create_oval(
                cabeza_x * self.TAM_CELDA + 1, cabeza_y * self.TAM_CELDA + 1,
                (cabeza_x + 1) * self.TAM_CELDA - 1,
                (cabeza_y + 1) * self.TAM_CELDA - 1,
                outline="#67e8f9", width=2,
            )
        self.dibujar_aviso()
        if self.portal_activo:
            self.dibujar_portal()
        if regla.get("niebla"):
            self.dibujar_niebla(fondo)
        if self.pausado:
            ancho = self.COLUMNAS * self.TAM_CELDA
            alto = self.FILAS * self.TAM_CELDA
            self.lienzo.create_rectangle(55, alto // 2 - 54, ancho - 55, alto // 2 + 54,
                                         fill="#17212b", outline="#f8fafc", width=2)
            self.lienzo.create_text(ancho // 2, alto // 2 - 18, text="PAUSA",
                                    fill="#f8fafc", font=("Arial", 20, "bold"))
            self.lienzo.create_text(ancho // 2, alto // 2 + 18,
                                    text="Enter o Espacio para seguir",
                                    fill="#86efac", font=("Arial", 13, "bold"))

    def dibujar_portal(self):
        """Portal fijo en el centro: anillos concéntricos violeta y cian."""
        x, y = self.portal_pos
        inicio_x, inicio_y = x * self.TAM_CELDA, y * self.TAM_CELDA
        fin_x, fin_y = inicio_x + self.TAM_CELDA, inicio_y + self.TAM_CELDA
        self.lienzo.create_oval(inicio_x, inicio_y, fin_x, fin_y,
                                outline="#c4b5fd", width=3)
        self.lienzo.create_oval(inicio_x + 5, inicio_y + 5, fin_x - 5, fin_y - 5,
                                outline="#67e8f9", width=2)
        self.lienzo.create_oval(inicio_x + 9, inicio_y + 9, fin_x - 9, fin_y - 9,
                                fill="#2e1065", outline="")

    def dibujar_niebla(self, fondo):
        """Tapa todo lo lejos de la cabeza (tablero Niebla)."""
        cabeza_x, cabeza_y = self.vibora[0]
        radio = 4
        for x in range(self.COLUMNAS):
            for y in range(self.FILAS):
                if abs(x - cabeza_x) + abs(y - cabeza_y) > radio:
                    self.lienzo.create_rectangle(x * self.TAM_CELDA, y * self.TAM_CELDA,
                                                 (x + 1) * self.TAM_CELDA,
                                                 (y + 1) * self.TAM_CELDA,
                                                 fill=fondo, outline="")

    def dibujar_sombra(self, celda, color, ancho=2):
        """Solo contorno neón, sin relleno: así se ve que es una sombra."""
        x, y = celda
        self.lienzo.create_rectangle(x * self.TAM_CELDA + 2, y * self.TAM_CELDA + 2,
                                     (x + 1) * self.TAM_CELDA - 2,
                                     (y + 1) * self.TAM_CELDA - 2,
                                     outline=color, width=ancho)

    def dibujar_invocadas(self):
        """Guardianas: solo contorno neón. Depredadoras: cuerpo uniforme sin cabeza."""
        fondo = self.dim()["fondo"]
        for serpiente in self.serpientes:
            if serpiente.aliada:
                cuerpo = self.mezclar(self.COLOR_GUARDIANA, fondo, 0.55)
                cabeza = self.mezclar("#a7f3d0", fondo, 0.9)
                for segmento in serpiente.segmentos[1:]:
                    self.dibujar_sombra(segmento, cuerpo)
                self.dibujar_sombra(serpiente.cabeza, cabeza, ancho=3)
            else:
                base = serpiente.color or self.COLORES_DEPREDADORA[0]
                cuerpo = self.mezclar(base, fondo, 0.7)
                for segmento in serpiente.segmentos[1:]:
                    self.dibujar_celda(segmento, cuerpo, margen=3)
                self.dibujar_celda(serpiente.cabeza, cuerpo, margen=2)
                # Sin cabeza ni ojos: silueta uniforme con borde oscuro en cada segmento.
                for sx, sy in serpiente.segmentos:
                    bx, by = sx * self.TAM_CELDA, sy * self.TAM_CELDA
                    self.lienzo.create_rectangle(bx + 1, by + 1,
                                                 bx + self.TAM_CELDA - 1,
                                                 by + self.TAM_CELDA - 1,
                                                 outline="#7f1d1d")

    def dibujar_aviso(self):
        """Limpia el aviso superior cuando caduca; ya no tapa el tablero."""
        if getattr(self, "aviso_var", None) is None:
            return
        if not self.aviso or time.monotonic() >= self.aviso[3]:
            self.aviso_var.set("")

    def dibujar_celda(self, celda, color, margen=0):
        x, y = celda
        inicio_x = x * self.TAM_CELDA + margen
        inicio_y = y * self.TAM_CELDA + margen
        fin_x = (x + 1) * self.TAM_CELDA - margen
        fin_y = (y + 1) * self.TAM_CELDA - margen
        self.lienzo.create_rectangle(inicio_x, inicio_y, fin_x, fin_y, fill=color, outline="")

    def finalizar(self):
        if self.terminado:
            return
        self.terminado = True
        self.esperando_salida = False
        self.cancelar_movimiento()
        self.historial.append({
            "hora": datetime.now().strftime("%H:%M"),
            "duracion": int(time.monotonic() - self.inicio_partida),
            "niveles": self.puntos,
        })
        self.actualizar_historial()
        self.dibujar()
        ancho = self.COLUMNAS * self.TAM_CELDA
        alto = self.FILAS * self.TAM_CELDA
        self.lienzo.create_rectangle(55, alto // 2 - 54, ancho - 55, alto // 2 + 54,
                                     fill="#17212b", outline="#f8fafc", width=2)
        self.lienzo.create_text(ancho // 2, alto // 2 - 18, text=self.motivo_final or "¡Fin de la partida!",
                                fill="#f8fafc", font=("Arial", 20, "bold"))
        self.lienzo.create_text(ancho // 2, alto // 2 + 18, text="Presiona R para reiniciar",
                                fill="#86efac", font=("Arial", 13, "bold"))


if __name__ == "__main__":
    ventana = tk.Tk()
    juego = Vibora(ventana)
    ventana.mainloop()
