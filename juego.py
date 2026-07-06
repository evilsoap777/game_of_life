import pygame as game
import numpy as np
import sys

#GRID (AMBIENTE)
def createGrid():
    rows = max(1, height // CELL_SIZE)
    cols = max(1, width // CELL_SIZE)
    arr = np.zeros((rows, cols), dtype=int)
    return arr

#redibuja el grid en cada iteracion 
def drawGrid(grid, ticks):
    screen.fill(COLOR_BG)

    for x in range(0, width, CELL_SIZE): #en el rango de lo ancho (horizontal)
        game.draw.line(screen, COLOR_GRID, (x, 0), (x, height)) #dibuja desde arriba hacia abajo (vertical) 

    for y in range(0, height, CELL_SIZE):
        game.draw.line(screen, COLOR_GRID, (0, y), (width, y))

    ralive, calive = np.where(grid == 1) #delega busqueda a C

    posx = calive * CELL_SIZE
    posy = ralive * CELL_SIZE
    color_alive = getNeonAliveColor(ticks)

    for x, y in zip(posx, posy): #for plano, retorna tuples iterables
        rectangle = game.Rect(x, y, CELL_SIZE, CELL_SIZE)
        game.draw.rect(screen, color_alive, rectangle)

    drawStats()
    return

#en vez de rescribir valores en matriz grid
def updateGrid(grid):
    global created_cells, dead_cells

    #creamos una nueva con valores actualizados y retornamos actualizada para usar en siguiente iteracion

    #retorna matriz con numero de vecinos, si llega a ultima pos reintroduce en primera
    neighbours = (
        np.roll(grid, 1, axis=0) + #derecha (0=fila;1=columna)
        np.roll(grid, -1, axis=0) + #izquierda
        np.roll(grid, 1, axis=1) + #abajo
        np.roll(grid, -1, axis=1) + #arriba
        np.roll(np.roll(grid, 1, axis=0), 1, axis=1) + #derecha abajo 
        np.roll(np.roll(grid, 1, axis=0), -1, axis=1) + #derecha arriba 
        np.roll(np.roll(grid, -1, axis=0), 1, axis=1) + #izquierda abajo
        np.roll(np.roll(grid, -1, axis=0), -1, axis=1) #izquierda arriba
    )
    #mira celulas vivas del grid original
    living_cells = (grid==1)

    #aplica logica segun vecinos (mantener y crear)
    survived=survival(living_cells,neighbours)
    born=reproduction(living_cells,neighbours)

    #crea nuevo grid con posiciones vivas (para retornarlo en la siguiente)
    updated_grid = np.zeros_like(grid) #shape y type de array parametro
    updated_grid[survived|born] = 1

    created_cells += int(np.count_nonzero((grid == 0) & (updated_grid == 1)))
    dead_cells += int(np.count_nonzero((grid == 1) & (updated_grid == 0)))

    return updated_grid

def getNeonAliveColor(ticks):
    palette = [(0, 255, 255), (255, 0, 255), (255, 255, 0)]
    cycle = (ticks // 5) % 360
    position = cycle / 360.0 * (len(palette) - 1)
    index = int(position)
    blend = position - index
    color_a = palette[index]
    color_b = palette[(index + 1) % len(palette)]

    return tuple(
        int(color_a[i] + (color_b[i] - color_a[i]) * blend)
        for i in range(3)
    )

#REGLAS DE JUEGO (INTERACCION)
def survival(living_cell, neighbors):
    return living_cell & ((neighbors == 2) | (neighbors == 3)) #operadores para matriz entera (numpy)

def reproduction(living_cell, neighbors):
    return (~living_cell) & (neighbors == 3)

def subpopulation(living_cell, neighbors):
    return living_cell & (neighbors < 2)

def overpopulation(living_cell, neighbors):
    return living_cell & (neighbors > 3)

def createLifebyClick(grid):
    global created_cells

    x,y=game.mouse.get_pos() #tomar posicion del mouse
    columna,fila= x // CELL_SIZE, y // CELL_SIZE

    if 0 <= fila < grid.shape[0] and 0 <= columna < grid.shape[1]:
        if grid[fila, columna] == 0:
            created_cells += 1
        grid[fila, columna] = 1
    return

def clearGameState():
    global grid, created_cells, dead_cells, playing

    created_cells = 0
    dead_cells = 0
    grid = createGrid()
    playing = False


#INTERFAZ
def init_ui():
    global width, height, screen, start_btn, template_btn, options_btn, exit_btn, btn_font, menu_bg, frame_actual, tiempo_ultimo_frame, grid, template_cards, volume_slider_rect, fps_slider_rect

    if FULLSCREEN:
        info = game.display.Info()
        width = info.current_w
        height = info.current_h
        screen = game.display.set_mode((width, height), game.FULLSCREEN)
    else:
        screen = game.display.set_mode((width, height), game.RESIZABLE)
    button_width = min(360, max(240, width // 4))
    button_height = 48
    button_gap = 72

    quadrant_center_x = width // 4
    quadrant_center_y = height // 2 + height // 4
    total_group_height = (button_height * 4) + (button_gap * 3)

    button_x = int(quadrant_center_x - button_width // 2)
    button_y_start = int(quadrant_center_y - total_group_height // 2)

    start_btn = game.Rect(button_x, button_y_start, button_width, button_height)
    template_btn = game.Rect(button_x, button_y_start + button_gap, button_width, button_height)
    options_btn = game.Rect(button_x, button_y_start + button_gap * 2, button_width, button_height)
    exit_btn = game.Rect(button_x, button_y_start + button_gap * 3, button_width, button_height)

    btn_font = game.font.Font("assets/fonts/Corpta.otf", max(18, min(28, width // 55)))

    slider_width = min(620, width - 260)
    slider_x = (width - slider_width) // 2
    volume_slider_rect = game.Rect(slider_x, height // 2 - 80, slider_width, 88)
    fps_slider_rect = game.Rect(slider_x, height // 2 + 40, slider_width, 88)

    if menu_frames:
        menu_bg = [
            (game.transform.scale(img, (width, height)), delay)
            for img, delay in menu_frames
        ]
    else:
        menu_bg = []


    template_cards = []
    columns = 3
    rows = 2
    card_width = min(360, max(260, (width - 140) // columns))
    card_height = 180
    card_gap_x = 28
    card_gap_y = 28
    total_grid_width = (card_width * columns) + (card_gap_x * (columns - 1))
    total_grid_height = (card_height * rows) + (card_gap_y * (rows - 1))
    start_x = (width - total_grid_width) // 2
    start_y = max(140, (height - total_grid_height) // 2 - 20)

    for index in range(len(template_catalog)):
        col = index % columns
        row = index // columns
        x = start_x + col * (card_width + card_gap_x)
        y = start_y + row * (card_height + card_gap_y)
        template_cards.append(game.Rect(x, y, card_width, card_height))

    frame_actual = 0
    tiempo_ultimo_frame = game.time.get_ticks()
    grid = createGrid()

def createTemplateCatalog():
    return [
        {
            "title": "Glider Gun",
            "description": "Patron clasico que dispara gliders en el grid.",
            "image": "gosper_glider_gun.png",
            "template": [
                (5, 1), (5, 2), (6, 1), (6, 2),
                (5, 11), (6, 11), (7, 11),
                (4, 12), (8, 12), (3, 13), (9, 13),
                (3, 14), (9, 14), (6, 15),
                (4, 16), (8, 16), (5, 17), (6, 17), (7, 17), (6, 18),
                (3, 21), (4, 21), (5, 21), (3, 22), (4, 22), (5, 22),
                (2, 23), (6, 23), (1, 25), (2, 25), (6, 25), (7, 25),
                (3, 35), (4, 35), (3, 36), (4, 36),
            ],
        },
        {
            "title": "Pufferfish",
            "description": "Un \"shuttle\" que se mueve en el grid y genera vida estatica.",
            "image": "pufferfish.PNG",
            "template": [
                #borde superior, avanza a la izquierda
                (1, 11), (1, 3),
                (2, 12), (2, 11), (2, 10),
                (2, 4), (2, 3), (2, 2),

                (3, 13), (3, 12), (3, 9),
                (3, 5), (3, 2), (3, 1),

                (4, 11), (4, 10), (4, 9),
                (4, 5), (4, 4), (4, 3),

                (6, 10), (6, 4),

                (7, 12), (7, 9),
                (7, 5), (7, 2),

                (8, 14), (8, 8),
                (8, 6), (8, 0),

                (9, 14), (9, 13),
                (9, 8), (9, 6),
                (9, 1), (9, 0),

                (10, 8), (10, 6),

                (11, 11), (11, 9),
                (11, 5), (11, 3),

                (12, 10), (12, 4),

                # abajo, 5 filas de separación, avanza a la derecha
                (12, 21), (12, 29),

                (11, 20), (11, 21), (11, 22),
                (11, 28), (11, 29), (11, 30),

                (10, 19), (10, 20), (10, 23),
                (10, 27), (10, 30), (10, 31),

                (9, 21), (9, 22), (9, 23),
                (9, 27), (9, 28), (9, 29),

                (7, 22), (7, 28),

                (6, 20), (6, 23),
                (6, 27), (6, 30),

                (5, 18), (5, 24),
                (5, 26), (5, 32),

                (4, 18), (4, 19),
                (4, 24), (4, 26),
                (4, 31), (4, 32),

                (3, 24), (3, 26),

                (2, 21), (2, 23),
                (2, 27), (2, 29),

                (1, 22), (1, 28),

                # tercer puffer, avanza a la izquierda
                (1, 47), (1, 39),

                (2, 48), (2, 47), (2, 46),
                (2, 40), (2, 39), (2, 38),

                (3, 49), (3, 48), (3, 45),
                (3, 41), (3, 38), (3, 37),

                (4, 47), (4, 46), (4, 45),
                (4, 41), (4, 40), (4, 39),

                (6, 46), (6, 40),

                (7, 48), (7, 45),
                (7, 41), (7, 38),

                (8, 50), (8, 44),
                (8, 42), (8, 36),

                (9, 50), (9, 49),
                (9, 44), (9, 42),
                (9, 37), (9, 36),

                (10, 44), (10, 42),

                (11, 47), (11, 45),
                (11, 41), (11, 39),

                (12, 46), (12, 40),


                # cuarto puffer, avanza a la derecha
                (12, 57), (12, 65),

                (11, 56), (11, 57), (11, 58),
                (11, 64), (11, 65), (11, 66),

                (10, 55), (10, 56), (10, 59),
                (10, 63), (10, 66), (10, 67),

                (9, 57), (9, 58), (9, 59),
                (9, 63), (9, 64), (9, 65),

                (7, 58), (7, 64),

                (6, 56), (6, 59),
                (6, 63), (6, 66),

                (5, 54), (5, 60),
                (5, 62), (5, 68),

                (4, 54), (4, 55),
                (4, 60), (4, 62),
                (4, 67), (4, 68),

                (3, 60), (3, 62),

                (2, 57), (2, 59),
                (2, 63), (2, 65),

                (1, 58), (1, 64),

                # quinto puffer, avanza a la izquierda
                (1, 83), (1, 75),

                (2, 84), (2, 83), (2, 82),
                (2, 76), (2, 75), (2, 74),

                (3, 85), (3, 84), (3, 81),
                (3, 77), (3, 74), (3, 73),

                (4, 83), (4, 82), (4, 81),
                (4, 77), (4, 76), (4, 75),

                (6, 82), (6, 76),

                (7, 84), (7, 81),
                (7, 77), (7, 74),

                (8, 86), (8, 80),
                (8, 78), (8, 72),

                (9, 86), (9, 85),
                (9, 80), (9, 78),
                (9, 73), (9, 72),

                (10, 80), (10, 78),

                (11, 83), (11, 81),
                (11, 77), (11, 75),

                (12, 82), (12, 76),
            ]
        },
        {
            "title": "Queen Bee",
            "description": "Un generador de gliders que colisionan y se destruyen entre si.",
            "image": "queen_bee_shuttle_pair.png",
            "template": [  
                #borde superior izquierda
                (0, 23),
                (1, 22),
                (2, 22), (2, 23), (2, 24),
                (4, 13),
                (5, 12), (5, 14),
                (6, 12), (6, 13), (6, 15),
                (7, 12), (7, 13), (7, 15), (7, 16),
                (8, 12), (8, 13), (8, 15),
                (9, 2), (9, 3), (9, 12), (9, 14),
                (10, 1), (10, 3), (10, 13), (10, 18), (10, 19), (10, 20),
                (11, 1), (11, 18), (11, 19), (11, 20),
                (12, 0), (12, 1), (12, 17), (12, 21),
                (13, 16), (13, 22),
                (14, 17), (14, 21),
                (15, 18), (15, 19), (15, 20),
                (23, 16), (23, 17),
                (24, 17),
                (25, 14), (25, 15), (25, 16),
                (26, 14),

                #abajo 30 espacios
                (0, 53),
                (1, 52),
                (2, 52), (2, 53), (2, 54),
                (4, 43),
                (5, 42), (5, 44),
                (6, 42), (6, 43), (6, 45),
                (7, 42), (7, 43), (7, 45), (7, 46),
                (8, 42), (8, 43), (8, 45),
                (9, 32), (9, 33), (9, 42), (9, 44),
                (10, 31), (10, 33), (10, 43), (10, 48), (10, 49), (10, 50),
                (11, 31), (11, 48), (11, 49), (11, 50),
                (12, 30), (12, 31), (12, 47), (12, 51),
                (13, 46), (13, 52),
                (14, 47), (14, 51),
                (15, 48), (15, 49), (15, 50),
                (23, 46), (23, 47),
                (24, 47),
                (25, 44), (25, 45), (25, 46),
                (26, 44),

                #abajo 30 espacios
                (0, 83),
                (1, 82),
                (2, 82), (2, 83), (2, 84),
                (4, 73),
                (5, 72), (5, 74),
                (6, 72), (6, 73), (6, 75),
                (7, 72), (7, 73), (7, 75), (7, 76),
                (8, 72), (8, 73), (8, 75),
                (9, 62), (9, 63), (9, 72), (9, 74),
                (10, 61), (10, 63), (10, 73), (10, 78), (10, 79), (10, 80),
                (11, 61), (11, 78), (11, 79), (11, 80),
                (12, 60), (12, 61), (12, 77), (12, 81),
                (13, 76), (13, 82),
                (14, 77), (14, 81),
                (15, 78), (15, 79), (15, 80),
                (23, 76), (23, 77),
                (24, 77),
                (25, 74), (25, 75), (25, 76),
                (26, 74)
            ],
        },
        {
            "title": "Max",
            "description": "Un \"spacefiller\" que llena el grid con lineas.",
            "image": "max_spacefiller.png",
            "template": [
                (100, 40), (99, 41), (100, 41), (101, 41), (94, 42), (95, 42), (96, 42), 
                (101, 42), (102, 42), (93, 43), (96, 43), (97, 43), (98, 43), (101, 43), 
                (103, 43), (104, 43), (92, 44), (96, 44), (98, 44), (101, 44), (103, 44), 
                (92, 45), (97, 45), (99, 45), (101, 45), (103, 45), (105, 45), (106, 45), 
                (94, 46), (99, 46), (101, 46), (105, 46), (106, 46), (82, 47), (83, 47), 
                (84, 47), (85, 47), (91, 47), (93, 47), (98, 47), (102, 47), (104, 47), 
                (105, 47), (106, 47), (82, 48), (86, 48), (87, 48), (89, 48), (91, 48), 
                (92, 48), (93, 48), (95, 48), (96, 48), (106, 48), (107, 48), (82, 49), 
                (88, 49), (89, 49), (95, 49), (83, 50), (86, 50), (87, 50), (89, 50), (92, 50), 
                (95, 50), (97, 50), (98, 50), (89, 51), (91, 51), (93, 51), (95, 51), (97, 51), 
                (99, 51), (105, 51), (106, 51), (107, 51), (108, 51), (83, 52), (86, 52), (87, 52), 
                (89, 52), (92, 52), (95, 52), (98, 52), (99, 52), (101, 52), (103, 52), (104, 52), 
                (108, 52), (82, 53), (88, 53), (89, 53), (93, 53), (95, 53), (97, 53), (101, 53), 
                (102, 53), (108, 53), (82, 54), (86, 54), (87, 54), (89, 54), (91, 54), (92, 54), 
                (95, 54), (98, 54), (101, 54), (103, 54), (104, 54), (107, 54), (82, 55), (83, 55), 
                (84, 55), (85, 55), (91, 55), (93, 55), (95, 55), (97, 55), (99, 55), (101, 55), 
                (92, 56), (93, 56), (95, 56), (98, 56), (101, 56), (103, 56), (104, 56), (107, 56), 
                (95, 57), (101, 57), (102, 57), (108, 57), (83, 58), (84, 58), (94, 58), (95, 58), 
                (97, 58), (98, 58), (99, 58), (101, 58), (103, 58), (104, 58), (108, 58), (84, 59), 
                (85, 59), (86, 59), (88, 59), (92, 59), (97, 59), (99, 59), (105, 59), (106, 59), 
                (107, 59), (108, 59), (84, 60), (85, 60), (89, 60), (91, 60), (96, 60), (84, 61), 
                (85, 61), (87, 61), (89, 61), (91, 61), (93, 61), (98, 61), (87, 62), (89, 62), 
                (92, 62), (94, 62), (98, 62), (86, 63), (87, 63), (89, 63), (92, 63), (93, 63), 
                (94, 63), (97, 63), (88, 64), (89, 64), (94, 64), (95, 64), (96, 64), (89, 65), 
                (90, 65), (91, 65), (90, 66)
            ],
        }
    ]

def placeTemplate(grid, template, start_row, start_column):
    for col, row in template:
        if 0 <= start_row + row < grid.shape[0] and 0 <= start_column + col < grid.shape[1]:
            grid[start_row + row, start_column + col] = 1
    return grid

def drawButton(button_rect, text):
    COLOR_BOTON = (30, 30, 45)
    game.draw.rect(screen, COLOR_BOTON, button_rect)
    text_surface = btn_font.render(text, True, (255, 255, 255))
    screen.blit(text_surface, (
        button_rect.x + (button_rect.width - text_surface.get_width()) // 2,
        button_rect.y + (button_rect.height - text_surface.get_height()) // 2
    ))

def drawAnimatedBackground():
    global frame_actual, tiempo_ultimo_frame

    if menu_bg:
        imagen_frame, delay_frame = menu_bg[frame_actual]
        screen.blit(imagen_frame, (0, 0))

        tiempo_actual = game.time.get_ticks()
        if tiempo_actual - tiempo_ultimo_frame >= delay_frame:
            frame_actual = (frame_actual + 1) % len(menu_bg)
            tiempo_ultimo_frame = tiempo_actual
    else:
        screen.fill(COLOR_BG)

def showMenu():
    drawAnimatedBackground()
    drawButton(start_btn, "Iniciar Simulacion")
    drawButton(template_btn, "Cargar plantilla")
    drawButton(options_btn, "Opciones")
    drawButton(exit_btn, "Salir")

    return

def getTemplatePreviewSurface(image_name, size):
    if not image_name:
        return None

    if image_name not in template_image_cache:
        try:
            image_surface = game.image.load(f"assets/images/{image_name}")
            template_image_cache[image_name] = game.transform.scale(image_surface, size)
        except Exception:
            template_image_cache[image_name] = None

    return template_image_cache.get(image_name)

def showTemplates():
    global selected_template_index

    drawAnimatedBackground()

    title_font = game.font.Font("assets/fonts/Corpta.otf", 36)

    for index, card_rect in enumerate(template_cards):
        card_color = (35, 35, 45)
        if selected_template_index == index:
            card_color = (55, 85, 70)

        game.draw.rect(screen, card_color, card_rect)
        game.draw.rect(screen, (120, 120, 140), card_rect, 1)

        preview_rect = game.Rect(card_rect.x + 12, card_rect.y + 12, 100, card_rect.height - 24)
        preview_surface = getTemplatePreviewSurface(template_catalog[index]["image"], (preview_rect.width, preview_rect.height))
        if preview_surface is not None:
            screen.blit(preview_surface, preview_rect)
        else:
            game.draw.rect(screen, (50, 70, 120), preview_rect)
            game.draw.rect(screen, (150, 170, 210), preview_rect, 1)
            preview_text = game.font.Font(None, 18).render("Imagen", True, (220, 220, 220))
            screen.blit(preview_text, (preview_rect.x + 10, preview_rect.y + 34))

        text_area_width = card_rect.width - preview_rect.width - 36
        text_x = card_rect.x + preview_rect.width + 18
        text_y = card_rect.y + 20

        title_font = game.font.Font("assets/fonts/Corpta.otf", 24)
        title_surface = title_font.render(template_catalog[index]["title"], True, (255, 255, 255))
        screen.blit(title_surface, (text_x, text_y))

        desc_font = game.font.Font("assets/fonts/Corpta.otf", 18)
        desc_words = template_catalog[index]["description"].split()
        desc_lines = []
        current_line = ""
        for word in desc_words:
            test_line = f"{current_line} {word}".strip()
            if desc_font.size(test_line)[0] <= text_area_width - 8:
                current_line = test_line
            else:
                if current_line:
                    desc_lines.append(current_line)
                current_line = word
        if current_line:
            desc_lines.append(current_line)

        desc_y = card_rect.y + 66
        for line in desc_lines:
            desc_surface = desc_font.render(line, True, (200, 200, 200))
            screen.blit(desc_surface, (text_x, desc_y))
            desc_y += 20

    return

def drawStats():
    stats_font = game.font.Font(None, 24)
    text = f"Creadas: {created_cells}  Muertas: {dead_cells}"
    text_surface = stats_font.render(text, True, (255, 255, 255))
    panel_rect = game.Rect(width - text_surface.get_width() - 20, 20, text_surface.get_width() + 16, text_surface.get_height() + 10)
    game.draw.rect(screen, (20, 20, 30), panel_rect)
    game.draw.rect(screen, (90, 90, 110), panel_rect, 1)
    screen.blit(text_surface, (panel_rect.x + 8, panel_rect.y + 5))

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def getSliderValueFromPosition(x, slider_rect, min_value, max_value):
    relative_x = clamp(x - slider_rect.x, 0, slider_rect.width)
    ratio = relative_x / slider_rect.width
    return int(round(min_value + ratio * (max_value - min_value)))

def drawSlider(label, value, min_value, max_value, rect):
    label_surface = btn_font.render(label, True, (255, 255, 255))
    label_bg_rect = game.Rect(rect.x - 10, rect.y - 8, label_surface.get_width() + 20, label_surface.get_height() + 14)
    game.draw.rect(screen, (0, 0, 0), label_bg_rect)
    game.draw.rect(screen, (90, 90, 110), label_bg_rect, 1)
    screen.blit(label_surface, (rect.x, rect.y))

    track_rect = game.Rect(rect.x, rect.y + 42, rect.width, 10)
    game.draw.rect(screen, (60, 60, 80), track_rect)

    fill_width = int((value - min_value) / (max_value - min_value) * track_rect.width)
    fill_rect = game.Rect(track_rect.x, track_rect.y, fill_width, track_rect.height)
    game.draw.rect(screen, (70, 190, 170), fill_rect)

    handle_center = (track_rect.x + fill_width, track_rect.y + track_rect.height // 2)
    game.draw.circle(screen, (230, 230, 230), handle_center, 12)
    game.draw.circle(screen, (35, 35, 55), handle_center, 7)


    return track_rect

def applyVolume(new_volume):
    if game.mixer.get_init():
        normalized = new_volume / 100.0
        game.mixer.music.set_volume(normalized)
        button_sound.set_volume(normalized)

def showOptions():
    global volume_slider_rect, fps_slider_rect

    drawAnimatedBackground()

    slider_width = min(620, width - 260)
    slider_x = (width - slider_width) // 2
    volume_slider_rect = game.Rect(slider_x, height // 2 - 80, slider_width, 88)
    fps_slider_rect = game.Rect(slider_x, height // 2 + 40, slider_width, 88)

    drawSlider("Volumen", volume_value, 0, 100, volume_slider_rect)
    drawSlider("FPS", fps_value, 10, 120, fps_slider_rect)


#MUSICA
def play_menu_music():
    game.mixer.music.stop()
    game.mixer.music.load(menu_music)
    game.mixer.music.play(-1)

def play_game_music():
    game.mixer.music.stop()
    game.mixer.music.load(game_music)
    game.mixer.music.play(-1)


#CONSTANTES
#celda
CELL_SIZE = 10
COLOR_BG = (10, 10, 15)
COLOR_GRID = (30, 30, 40)
COLOR_DIE = (180, 50, 50)
COLOR_ALIVE = (0, 255, 130)

MENU_STATE = "menu"
GAME_STATE = "game"
OPTIONS_STATE = "options"
TEMPLATES_STATE = "templates"
DEFAULT_WIDTH = 1366
DEFAULT_HEIGHT = 768
FULLSCREEN = True

#VARIABLES
width = DEFAULT_WIDTH
height = DEFAULT_HEIGHT
screen = None
clock = game.time.Clock()
running = True
grid = createGrid()
playing = False
actual_state = MENU_STATE
created_cells = 0
dead_cells = 0
start_btn = None
template_btn = None
options_btn = None
exit_btn = None
btn_font = None
menu_frames = []
menu_bg = []
frame_actual = 0
tiempo_ultimo_frame = game.time.get_ticks()
selected_template_index = None
template_cards = []
template_image_cache = {}
volume_value = 70
fps_value = 50
volume_slider_rect = None
fps_slider_rect = None
volume_dragging = False
fps_dragging = False

game.font.init()
game.mixer.init()
button_sound = game.mixer.Sound("assets/sounds/button_sound.wav")
menu_music = "assets/sounds/computronium.mp3"
game_music = "assets/sounds/the_world.mp3"



play_menu_music()
menu_frames = game.image.load_animation("assets\\images\\game-of-life-loop.gif")
game.display.set_caption("Game of life")
game.init()
template_catalog = createTemplateCatalog()
init_ui()


#BUCLE PRINCIPAL
#en cada vuelta de ciclo la pantalla se borra por completo y se dibuja de nuevo, con posibles datos actualizados

while running:
    previous_state = actual_state

    # capturar todos los eventos (clics, teclas, etc.)
    for event in game.event.get(): #modulo evento

        if event.type == game.QUIT: #constante QUIT
            running=False

        if event.type == game.VIDEORESIZE:
            width, height = event.w, event.h
            init_ui()
            continue

        mouse = game.mouse.get_pos()
        if actual_state == MENU_STATE:
            if event.type == game.KEYDOWN and event.key == game.K_ESCAPE:
                running = False

            if event.type == game.MOUSEBUTTONDOWN and event.button == 1:

                if start_btn.collidepoint(mouse):
                    button_sound.play()
                    actual_state = GAME_STATE
                    game.mixer.music.stop()
                    playing = False
                    
                elif template_btn.collidepoint(mouse):
                    button_sound.play()
                    selected_template_index = None
                    actual_state = TEMPLATES_STATE

                elif options_btn.collidepoint(mouse):
                    button_sound.play()
                    actual_state = OPTIONS_STATE

                elif exit_btn.collidepoint(mouse):
                    running=False

        elif actual_state == TEMPLATES_STATE:
            if event.type == game.KEYDOWN and event.key == game.K_ESCAPE:
                play_menu_music()
                actual_state = MENU_STATE

            if event.type == game.MOUSEBUTTONDOWN and event.button == 1:
                for index, card_rect in enumerate(template_cards):
                    if card_rect.collidepoint(mouse):
                        button_sound.play()
                        selected_template_index = index
                        grid = createGrid()
                        placeTemplate(grid, template_catalog[index]["template"], 10, 10)
                        actual_state = GAME_STATE
                        playing = False
                        game.mixer.music.stop()
                        break

        elif actual_state == OPTIONS_STATE:
            if event.type == game.KEYDOWN and event.key == game.K_ESCAPE:
                play_menu_music()
                actual_state = MENU_STATE

            if event.type == game.MOUSEBUTTONDOWN and event.button == 1:
                if volume_slider_rect and volume_slider_rect.collidepoint(mouse):
                    volume_dragging = True
                    volume_value = getSliderValueFromPosition(mouse[0], volume_slider_rect, 0, 100)
                    applyVolume(volume_value)
                elif fps_slider_rect and fps_slider_rect.collidepoint(mouse):
                    fps_dragging = True
                    fps_value = getSliderValueFromPosition(mouse[0], fps_slider_rect, 10, 120)

            if event.type == game.MOUSEBUTTONUP and event.button == 1:
                volume_dragging = False
                fps_dragging = False

            if event.type == game.MOUSEMOTION:
                if volume_dragging and volume_slider_rect:
                    volume_value = getSliderValueFromPosition(mouse[0], volume_slider_rect, 0, 100)
                    applyVolume(volume_value)
                elif fps_dragging and fps_slider_rect:
                    fps_value = getSliderValueFromPosition(mouse[0], fps_slider_rect, 10, 120)

        elif actual_state == GAME_STATE:
            if event.type == game.KEYDOWN:
                
                if event.key == game.K_SPACE:
                    playing = not playing
                    clock.tick(100)

                    if playing:
                        play_game_music()
                    else:
                        game.mixer.music.stop()

                if event.key == game.K_ESCAPE:
                    play_menu_music()
                    actual_state = MENU_STATE

            if event.type == game.MOUSEBUTTONDOWN and event.button == 1:
                createLifebyClick(grid)
                    
    if previous_state == GAME_STATE and actual_state != GAME_STATE:
        clearGameState()

    if actual_state==GAME_STATE and game.mouse.get_pressed()[0]:
        createLifebyClick(grid)

    match actual_state:
        case "game":
            if playing:
                grid = updateGrid(grid)
        case _:
            pass
    
    if actual_state == MENU_STATE:
        showMenu()
    elif actual_state == TEMPLATES_STATE:
        showTemplates()
    elif actual_state == OPTIONS_STATE:
        showOptions()
    elif actual_state == GAME_STATE:
        drawGrid(grid, game.time.get_ticks()) #redibuja la pantalla cada iteracion
    
    game.display.flip() #modulo display
    if actual_state == GAME_STATE and playing:
        clock.tick(fps_value)
    else:
        clock.tick(50)

