# Viborita clásica

Juego clásico de la viborita hecho con Python y Tkinter. Come las píldoras de colores, crece con cada una y evita chocar contra los bordes o contra tu propio cuerpo.

## Requisitos

- Python 3.8 o superior
- Tkinter (incluido en la mayoría de instalaciones de Python; en Linux puede requerir `sudo apt install python3-tk`)

No necesita dependencias externas.

## Cómo ejecutarlo

```bash
python3 Untitled-1.py
```

## Controles

- **Flechas**: mover la viborita (no puedes girar en sentido contrario de inmediato).
- **R**: reiniciar tras terminar la partida.

## Reglas

- Cada píldora suma 1 punto y hace que la viborita crezca.
- La velocidad aumenta un poco con cada píldora, hasta un límite.
- La partida termina si la cabeza sale del tablero o choca con el cuerpo.
