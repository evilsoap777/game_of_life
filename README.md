# Game of Life

Este proyecto es una implementación interactiva del juego de la vida de Conway usando Python y Pygame.

## Descripción

- `juego.py` es el archivo principal.
- Usa Pygame para mostrar un grid animado con células vivas y muertas.
- Incluye menú principal, opciones, selección de plantillas y un modo de simulación.
- Permite colocar células con el mouse y ajustar la velocidad (FPS) y el volumen.

## Requisitos

- Python 3.7+ (recomendado)
- Pygame
- NumPy

## Instalación

1. Asegúrate de tener Python instalado.
2. Instala las dependencias:

```bash
pip install pygame-ce numpy
```

## Uso

Desde la carpeta del proyecto, ejecuta:

```bash
python juego.py
```

## Controles

- `Clic izquierdo`: coloca una célula viva en la celda seleccionada.
- `Espacio`: iniciar / pausar la simulación.
- `Esc`: volver al menú principal o salir desde el menú.

## Menú y funciones

- `Iniciar Simulacion`: abre la ventana de simulación.
- `Cargar plantilla`: selecciona una configuración inicial predefinida.
- `Opciones`: ajusta volumen y FPS.
- `Salir`: cierra la aplicación.

## Plantillas disponibles

- `Glider Gun`: patrón clásico que genera gliders.
- `Pufferfish`: un shuttle que deja huella en el grid.
- `Queen Bee`: generador de gliders con colisiones.
- `Max`: un spacefiller que crea líneas de células.

## Estructura de archivos

- `juego.py`: código principal del juego.
- `assets/fonts`: tipografías usadas.
- `assets/images`: imágenes y animaciones de fondo.
- `assets/sounds`: sonidos y música del juego.

## Notas

- El juego se ejecuta en pantalla completa por defecto.
- Si no deseas pantalla completa, puedes cambiar la constante `FULLSCREEN` en `juego.py`.
