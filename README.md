# Viborita clásica

Juego clásico de la viborita hecho con Python y Tkinter, con eventos legendarios cada 10 niveles (sombras guardianas aliadas y depredadoras enemigas), 10 tableros nocturnos conectados por portales cada 25 niveles, pausa in-game y controles alternativos (WASD y teclado numérico). Come las píldoras de colores, crece con cada una y evita chocar contra los bordes o contra tu propio cuerpo.

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
- **WASD** (W arriba, S abajo, A izquierda, D derecha) y **teclado numérico** (8, 4, 6, 2): lo mismo que las flechas.
- **Enter o Espacio**: pausar y reanudar la partida.
- **R**: reiniciar tras terminar la partida.

## Reglas

- Cada píldora concede experiencia (mínimo +1) y hace que la viborita crezca. Los niveles acumulados y las píldoras consumidas se muestran por separado.
- La velocidad aumenta un poco con cada píldora y puede cambiar por los efectos adquiridos.
- Un choque contra pared o cuerpo termina la partida, salvo que tengas una carga de escudo y una salida segura.

## Eventos legendarios: el equilibrio de las sombras

Cada vez que los niveles (XP) cruzan un múltiplo de 10 (10, 20, 30…) se procesa un evento, una sola vez por hito, aunque un salto cruce varios. Se sortea:

- **Sombra Guardiana (buff, 50%):** solo contorno neón turquesa, sin relleno (cabeza más brillante). Come píldoras (+1 nivel cada una), crece y puede comerse a las depredadoras al alcanzarlas (les quita un segmento). Si una depredadora la roza, la devora de un golpe. La jugadora la atraviesa sin efecto. Rebota en las paredes y, si queda atrapada, atraviesa cuerpos (nunca paredes): se mueve sin fin.
- **Sombra Depredadora (debuff, 50%):** cuerpo uniforme sin cabeza ni ojos, de color aleatorio (carmesí, violeta, magenta, naranja o ámbar). Se mueve al azar (50%), persigue a la jugadora (35%) o busca píldoras (15%). No puede dañar a la jugadora: solo la jugadora se la puede comer. En cambio, devora guardianas de un roce. Si queda atrapada, espera quieta.

Las invocadas se acumulan (tope de 12 a la vez; si no cabe o no hay hueco, quedan pendientes). Nunca aparecen sobre la jugadora ni cerca de su cabeza.

Combate con depredadoras:
- Solo tú las puedes comer: tu cabeza en su cuerpo (costado, cola o frontal) les quita un segmento (+1 nivel por golpe). Sin bonus extra: una enemiga de 3 segmentos te da 3 niveles en total.
- Ellas no te dañan: sus choques te atraviesan sin quitarte nada ni gastarte el escudo.
- Ellas devoran a tus guardianas de un roce (la guardiana desaparece, sin premio).
- El aviso legendario aparece arriba del tablero, sin tapar el mapa.
- Las paredes y tu propio cuerpo siguen siendo letales.

Los parámetros (probabilidades, tope, premios) están como constantes al inicio de la clase `Vibora`.

## Dimensiones y portales

Cada 25 niveles (25, 50, 75…) aparece un portal fijo en el centro del tablero (anillos violeta y cian, siempre visible). Al viajar, el próximo portal aparece 25 niveles después: si viajas en el 67, el siguiente sale en el 75. Si no viajas, el portal sigue ahí. Cruzarlo es opcional: solo viajas si pasas tu cabeza por él, en orden cíclico del 1 al 10 y de vuelta al 1. El marcador avisa si el portal está listo o en qué nivel sale.

- Cada tablero congela su estado en memoria: víbora, píldoras, sombras e invocaciones pendientes quedan como las dejaste. Al volver, todo sigue igual.
- Los niveles, la XP y tus poderes (escudos, magnetismo…) son globales de la sesión.
- Al llegar a un tablero nuevo no viajas de inmediato aunque nazcas sobre el portal: hay un enfriamiento de 3 ticks.
- El portal no recibe píldoras ni invocaciones encima.

Los 10 tableros (modo nocturno, cada uno con su color):

1. **Base:** igual que ahora.
2. **Envolvente:** los bordes conectan con el lado opuesto.
3. **Vértigo:** velocidad base más alta.
4. **Sereno:** más lento y con 3 píldoras a la vez.
5. **Sombrío:** eventos legendarios con menos guardianas (25% buff).
6. **Luminoso:** eventos con más guardianas (75% buff).
7. **Errante:** las píldoras se mueven una celda cada 5 ticks.
8. **Espejo:** las píldoras se ven reflejadas en horizontal (las ves a un lado pero están en el opuesto); los controles son normales.
9. **Niebla:** solo se ve alrededor de tu cabeza.
10. **Puro:** sin buffs ni debuffs, solo píldoras y sombras.

## Historial de la sesión

- Los niveles registran la experiencia acumulada; se empieza con cero y cada píldora concede +1 salvo bonificaciones.
- Al perder se registra la hora de finalización, la duración y los niveles avanzados.
- El panel neón muestra primero las partidas recientes y el total de niveles acumulados.
- Aparece arriba a la izquierda cuando hay espacio fuera del tablero (por ejemplo, al maximizar). Si no hay espacio, se oculta, pero sigue registrando las partidas.
- Puedes desplazarte por el historial usando su barra lateral.
- Reiniciar con **R** conserva los resultados. Cerrar el programa los borra: no se guardan en disco.

## Pruebas

Ejecuta `python3 -m unittest discover -s tests -v`. Las pruebas no necesitan una pantalla.

## Buffs y debuffs

Cada píldora consumida sortea un efecto: 50% de buff y 50% de debuff, con seis opciones equiprobables por categoría (aproximadamente 8,33% por efecto). Los efectos sin cambios por alcanzar un límite se registran y no se vuelven a sortear.

- **Multiplicidad (buff):** añade una píldora disponible durante la partida. Se acumula y las píldoras restantes se conservan al comer otra.
- **Ralentización (buff):** reduce un 10% la velocidad actual después del aumento normal de dificultad.
- **Acortamiento (buff):** después de crecer por el consumo, retira dos segmentos: quedas una celda más corto que antes de comer. Si antes de comer tenías la longitud inicial (3 celdas), no se activa y conservas el crecimiento normal. No modifica puntos ni niveles.
- **Escudo protector (buff):** añade una carga acumulable. Un choque consume una carga y cancela el movimiento, sin atravesar el obstáculo. El juego espera a que elijas con las flechas (o WASD/numérico) una dirección segura; si no existe ninguna dirección legal, termina la partida. Un halo cian indica que hay escudo.
- **Experiencia aumentada (buff):** suma +1 a la experiencia por píldora desde el siguiente consumo: +1, +2, +3… No añade crecimiento, dificultad ni sorteos adicionales.
- **Magnetismo (buff):** aumenta el radio de recogida Manhattan en una celda, hasta el máximo útil del tablero. Radio 1 incluye los cuatro vecinos; las diagonales necesitan radio 2. Un contorno indica el alcance. Con radio activo también te comes un segmento enemigo a distancia (uno por tick, y solo si no comiste píldora; las guardianas aliadas no se comen).
- **Aceleración (debuff):** aumenta un 10% la velocidad actual después del aumento normal de dificultad.
- **Píldora escurridiza (debuff):** añade una carga que hace escapar la siguiente píldora que intentas comer. No creces ni sumas puntos o niveles en ese intento. Si no hay otra celda libre, se permite comer y se consume la carga.
- **Crecimiento extra (debuff):** añade un segmento además del crecimiento normal. Si no puede extender la cola de forma segura, acumula una carga para conservarla en un movimiento posterior. No concede puntos adicionales. Una carga pendiente también puede aplicarse cuando una píldora escapa.
- **Ruptura de escudo (debuff):** elimina una carga, sin bajar de cero ni terminar la partida.
- **Experiencia reducida (debuff):** reduce en uno la experiencia por píldora desde el siguiente consumo, con mínimo +1. No resta experiencia anterior.
- **Antimagnetismo (debuff):** reduce el radio en uno, con mínimo cero (contacto directo). No impide comer ni genera penalizaciones futuras.

El magnetismo recoge como máximo una píldora por movimiento: contacto directo primero, después la más cercana y, en empate, menor columna y fila. Una píldora escurridiza también puede escapar de una recogida magnética; no se recoge otra en su lugar ni se vuelve a recoger la teleportada durante el mismo movimiento. Los choques se resuelven antes de consumir píldoras o activar trampas.

Los intervalos de movimiento están limitados entre 25 y 500 ms. Las píldoras nunca aparecen sobre el cuerpo ni sobre otras píldoras, y su cantidad se limita al espacio libre.

Al ampliar suficientemente la ventana, aparecen dos paneles a la derecha: buffs verdes arriba y debuffs rojos debajo. Muestran las acumulaciones, el estado actual y un registro desplazable. Se ocultan si no caben sin tapar el tablero; los efectos siguen activos.

Los paneles también muestran la longitud actual, la inicial y el crecimiento pendiente. Cuando hay crecimiento pendiente, la cola no se retira: entrar en su celda es una colisión.

Al perder, los efectos quedan visibles. **R** restaura la longitud inicial y reinicia todos los efectos, las cargas y su registro, pero conserva el historial de partidas de la sesión.
