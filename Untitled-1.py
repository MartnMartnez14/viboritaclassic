"""Juego clásico de la viborita, hecho con Tkinter."""

import math
import random
import tkinter as tk


class Vibora:
    """Controla el tablero, el movimiento y el estado de una partida."""

    TAM_CELDA = 25
    COLUMNAS = 24
    FILAS = 20
    VELOCIDAD_INICIAL = 145
    VELOCIDAD_MINIMA = 55
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
            font=("Arial", 14, "bold"),
            bg="#050711",
            fg="#f8fafc",
            padx=12,
            pady=10,
        ).pack(fill="x")

        self.lienzo = tk.Canvas(
            self.panel,
            width=self.COLUMNAS * self.TAM_CELDA,
            height=self.FILAS * self.TAM_CELDA,
            bg="#101820",
            highlightthickness=0,
        )
        self.lienzo.pack(padx=12, pady=(0, 12))

        self.raiz.bind("<KeyPress>", self.tecla_presionada)
        self.reiniciar()
        self.animar_cielo()

    def ajustar_cielo(self, evento):
        """Adapta las estrellas y centra el juego al cambiar la ventana."""
        self.fondo.coords(self.panel_id, evento.width / 2, evento.height / 2)
        for item, x, y, radio, *_ in self.estrellas:
            px, py = x * evento.width, y * evento.height
            self.fondo.coords(item, px - radio, py - radio, px + radio, py + radio)

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

    def cerrar(self):
        """Cancela los destellos antes de cerrar la ventana."""
        if self.animacion_cielo is not None:
            self.raiz.after_cancel(self.animacion_cielo)
        self.raiz.destroy()

    def reiniciar(self):
        """Devuelve todos los valores al comienzo de una partida."""
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
        self.velocidad = self.VELOCIDAD_INICIAL
        self.terminado = False
        self.paleta_colores = list(self.PALETA_INICIAL)
        self.comida = self.crear_comida()
        self.actualizar_marcador()
        self.dibujar()
        self.raiz.after(self.velocidad, self.avanzar)

    def tecla_presionada(self, evento):
        """Cambia de dirección o reinicia una partida terminada."""
        tecla = evento.keysym
        if self.terminado:
            if tecla.lower() == "r":
                self.reiniciar()
            return

        if tecla in self.DIRECCIONES and tecla != self.OPUESTAS[self.direccion]:
            self.siguiente_direccion = tecla

    def avanzar(self):
        """Mueve una celda y programa el siguiente movimiento."""
        if self.terminado:
            return

        self.direccion = self.siguiente_direccion
        dx, dy = self.DIRECCIONES[self.direccion]
        cabeza_x, cabeza_y = self.vibora[0]
        nueva_cabeza = (cabeza_x + dx, cabeza_y + dy)
        comio = nueva_cabeza == self.comida

        fuera_del_tablero = not (
            0 <= nueva_cabeza[0] < self.COLUMNAS
            and 0 <= nueva_cabeza[1] < self.FILAS
        )
        cuerpo_a_revisar = self.vibora if comio else self.vibora[:-1]
        if fuera_del_tablero or nueva_cabeza in cuerpo_a_revisar:
            self.finalizar()
            return

        self.vibora.insert(0, nueva_cabeza)
        if comio:
            self.puntos += 1
            self.velocidad = max(self.VELOCIDAD_MINIMA, self.velocidad - 4)
            self.paleta_colores.append(self.color_comida)
            self.comida = self.crear_comida()
            self.actualizar_marcador()
        else:
            self.vibora.pop()

        self.dibujar()
        self.raiz.after(self.velocidad, self.avanzar)

    def crear_comida(self):
        """Elige una celda libre y un color vibrante para la píldora."""
        libres = [
            (x, y)
            for x in range(self.COLUMNAS)
            for y in range(self.FILAS)
            if (x, y) not in self.vibora
        ]
        self.color_comida = random.choice(self.COLORES_PILDORA)
        return random.choice(libres)

    def actualizar_marcador(self):
        self.puntos_var.set(f"Puntos: {self.puntos}   |   Flechas para mover")

    def dibujar(self):
        """Redibuja el tablero para reflejar el estado actual."""
        self.lienzo.delete("all")
        for x in range(0, self.COLUMNAS * self.TAM_CELDA, self.TAM_CELDA):
            self.lienzo.create_line(x, 0, x, self.FILAS * self.TAM_CELDA, fill="#1e2d38")
        for y in range(0, self.FILAS * self.TAM_CELDA, self.TAM_CELDA):
            self.lienzo.create_line(0, y, self.COLUMNAS * self.TAM_CELDA, y, fill="#1e2d38")

        self.dibujar_celda(self.comida, self.color_comida, margen=4)
        for indice, segmento in enumerate(self.vibora):
            color = "#dcfce7" if indice == 0 else self.paleta_colores[(indice - 1) % len(self.paleta_colores)]
            self.dibujar_celda(segmento, color, margen=2)

    def dibujar_celda(self, celda, color, margen=0):
        x, y = celda
        inicio_x = x * self.TAM_CELDA + margen
        inicio_y = y * self.TAM_CELDA + margen
        fin_x = (x + 1) * self.TAM_CELDA - margen
        fin_y = (y + 1) * self.TAM_CELDA - margen
        self.lienzo.create_rectangle(inicio_x, inicio_y, fin_x, fin_y, fill=color, outline="")

    def finalizar(self):
        self.terminado = True
        self.dibujar()
        ancho = self.COLUMNAS * self.TAM_CELDA
        alto = self.FILAS * self.TAM_CELDA
        self.lienzo.create_rectangle(55, alto // 2 - 54, ancho - 55, alto // 2 + 54,
                                     fill="#17212b", outline="#f8fafc", width=2)
        self.lienzo.create_text(ancho // 2, alto // 2 - 18, text="¡Fin de la partida!",
                                fill="#f8fafc", font=("Arial", 20, "bold"))
        self.lienzo.create_text(ancho // 2, alto // 2 + 18, text="Presiona R para reiniciar",
                                fill="#86efac", font=("Arial", 13, "bold"))


if __name__ == "__main__":
    ventana = tk.Tk()
    juego = Vibora(ventana)
    ventana.mainloop()
