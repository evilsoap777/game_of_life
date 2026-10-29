import numpy as np

MIN_CELL_SIZE = 1
MAX_CELL_SIZE = 25


class GameEngine:
    def __init__(self, width=1366, height=768, cell_size=4):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.generations = 0
        self.created_cells = 0
        self.dead_cells = 0
        # El mundo vive a la resolucion maxima (cell_size = 1) y la camara
        # selecciona la ventana visible. Asi el zoom nunca descarta celdas.
        self.camera_x = 0
        self.camera_y = 0
        self.world = None
        self._ensure_world()

    def view_rows(self):
        return max(1, self.height // self.cell_size)

    def view_cols(self):
        return max(1, self.width // self.cell_size)

    def _ensure_world(self):
        # El mundo nunca se encoge: crece para cubrir la pantalla a zoom maximo.
        rows = max(1, self.height)
        cols = max(1, self.width)
        if self.world is not None:
            world_rows, world_cols = self.world.shape
            rows = max(rows, world_rows)
            cols = max(cols, world_cols)
            if (rows, cols) == (world_rows, world_cols):
                return

        new_world = np.zeros((rows, cols), dtype=np.uint8)
        if self.world is not None:
            new_world[:self.world.shape[0], :self.world.shape[1]] = self.world
        self.world = new_world

    def _clamp_camera(self):
        max_x = max(0, self.world.shape[1] - self.view_cols())
        max_y = max(0, self.world.shape[0] - self.view_rows())
        self.camera_x = min(max(0, self.camera_x), max_x)
        self.camera_y = min(max(0, self.camera_y), max_y)

    def view(self):
        self._ensure_world()
        self._clamp_camera()
        return self.world[
            self.camera_y:self.camera_y + self.view_rows(),
            self.camera_x:self.camera_x + self.view_cols(),
        ]

    def resize_viewport(self, width, height):
        self.width = width
        self.height = height
        self._ensure_world()
        self._clamp_camera()

    def set_cell_size(self, new_cell_size):
        new_cell_size = max(MIN_CELL_SIZE, min(MAX_CELL_SIZE, new_cell_size))
        if new_cell_size == self.cell_size:
            return False

        # Mantener el centro de la vista fijo mientras se hace zoom.
        center_x = self.camera_x + self.view_cols() / 2.0
        center_y = self.camera_y + self.view_rows() / 2.0
        self.cell_size = new_cell_size
        self._ensure_world()
        self.camera_x = int(round(center_x - self.view_cols() / 2.0))
        self.camera_y = int(round(center_y - self.view_rows() / 2.0))
        self._clamp_camera()
        return True

    def set_camera(self, x, y):
        self.camera_x = x
        self.camera_y = y
        self._clamp_camera()

    def update_grid(self):
        world = self.world

        # Solo puede cambiar el recuadro que contiene vida mas un margen de 1.
        # Fuera de ahi todas las celdas estan muertas y no pueden nacer.
        live_rows = np.flatnonzero(world.any(axis=1))
        if live_rows.size == 0:
            self.generations += 1
            return self.view()
        live_cols = np.flatnonzero(world.any(axis=0))
        r0, r1 = int(live_rows[0]), int(live_rows[-1])
        c0, c1 = int(live_cols[0]), int(live_cols[-1])

        # Si la vida toca un borde del mundo, la influencia da la vuelta y hay
        # que recalcular ese eje completo. Si no, basta el recuadro + 1.
        if r0 == 0 or r1 == world.shape[0] - 1:
            rr0, rr1 = 0, world.shape[0]
        else:
            rr0, rr1 = r0 - 1, r1 + 2
        if c0 == 0 or c1 == world.shape[1] - 1:
            cc0, cc1 = 0, world.shape[1]
        else:
            cc0, cc1 = c0 - 1, c1 + 2

        # Recuadro activo mas su borde de 1 celda, con envoltura toroidal
        # calculada sobre el mundo completo (no sobre el recuadro).
        row_idx = np.arange(rr0 - 1, rr1 + 1) % world.shape[0]
        col_idx = np.arange(cc0 - 1, cc1 + 1) % world.shape[1]
        padded = world[np.ix_(row_idx, col_idx)]

        # Las 8 vistas desplazadas se suman en uint8 (maximo 8, sin desbordar).
        neighbours = (
            padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:] +
            padded[1:-1, :-2] + padded[1:-1, 2:] +
            padded[2:, :-2] + padded[2:, 1:-1] + padded[2:, 2:]
        )

        sub = padded[1:-1, 1:-1]
        living_cells = sub == 1
        survived = living_cells & (neighbours == 2)
        born = neighbours == 3

        # Las estadisticas se derivan de las mascaras ya calculadas.
        self.created_cells += int(np.count_nonzero(born & ~living_cells))
        self.dead_cells += int(np.count_nonzero(living_cells & ~survived))
        self.generations += 1

        # Escritura en sitio: el nuevo estado ya se calculo por completo.
        world[rr0:rr1, cc0:cc1] = survived | born
        return self.view()

    def survival(self, living_cell, neighbors):
        return living_cell & ((neighbors == 2) | (neighbors == 3))

    def reproduction(self, living_cell, neighbors):
        return (~living_cell) & (neighbors == 3)

    def subpopulation(self, living_cell, neighbors):
        return living_cell & (neighbors < 2)

    def overpopulation(self, living_cell, neighbors):
        return living_cell & (neighbors > 3)

    def _world_coords(self, x, y):
        return self.camera_y + y // self.cell_size, self.camera_x + x // self.cell_size

    def create_life_by_click(self, x, y):
        fila, columna = self._world_coords(x, y)
        if 0 <= fila < self.world.shape[0] and 0 <= columna < self.world.shape[1]:
            if self.world[fila, columna] == 0:
                self.created_cells += 1
            self.world[fila, columna] = 1

    def delete_life_by_click(self, x, y):
        fila, columna = self._world_coords(x, y)
        if 0 <= fila < self.world.shape[0] and 0 <= columna < self.world.shape[1]:
            self.world[fila, columna] = 0

    def randomize_grid(self):
        self.world = (np.random.random(self.world.shape) < 0.2).astype(np.uint8)
        self.created_cells += int(np.count_nonzero(self.world))
        self.generations = 0

    def clear_game_state(self):
        self.created_cells = 0
        self.dead_cells = 0
        self.generations = 0
        self.cell_size = 4
        self.camera_x = 0
        self.camera_y = 0
        self.world.fill(0)

    def create_template_catalog(self):
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
                ],
            },
            {
                "title": "Queen Bee",
                "description": "Un generador de gliders que colisionan y se destruyen entre si.",
                "image": "queen_bee_shuttle_pair.png",
                "template": [
                    (0, 23), (1, 22), (2, 22), (2, 23), (2, 24),
                    (4, 13), (5, 12), (5, 14), (6, 12), (6, 13), (6, 15),
                    (7, 12), (7, 13), (7, 15), (7, 16), (8, 12), (8, 13), (8, 15),
                    (9, 2), (9, 3), (9, 12), (9, 14), (10, 1), (10, 3), (10, 13),
                    (10, 18), (10, 19), (10, 20), (11, 1), (11, 18), (11, 19), (11, 20),
                    (12, 0), (12, 1), (12, 17), (12, 21), (13, 16), (13, 22),
                    (14, 17), (14, 21), (15, 18), (15, 19), (15, 20),
                    (23, 16), (23, 17), (24, 17), (25, 14), (25, 15), (25, 16), (26, 14),
                    (0, 53), (1, 52), (2, 52), (2, 53), (2, 54),
                    (4, 43), (5, 42), (5, 44), (6, 42), (6, 43), (6, 45),
                    (7, 42), (7, 43), (7, 45), (7, 46), (8, 42), (8, 43), (8, 45),
                    (9, 32), (9, 33), (9, 42), (9, 44), (10, 31), (10, 33), (10, 43),
                    (10, 48), (10, 49), (10, 50), (11, 31), (11, 48), (11, 49), (11, 50),
                    (12, 30), (12, 31), (12, 47), (12, 51), (13, 46), (13, 52),
                    (14, 47), (14, 51), (15, 48), (15, 49), (15, 50),
                    (23, 46), (23, 47), (24, 47), (25, 44), (25, 45), (25, 46), (26, 44),
                    (0, 83), (1, 82), (2, 82), (2, 83), (2, 84),
                    (4, 73), (5, 72), (5, 74), (6, 72), (6, 73), (6, 75),
                    (7, 72), (7, 73), (7, 75), (7, 76), (8, 72), (8, 73), (8, 75),
                    (9, 62), (9, 63), (9, 72), (9, 74), (10, 61), (10, 63), (10, 73),
                    (10, 78), (10, 79), (10, 80), (11, 61), (11, 78), (11, 79), (11, 80),
                    (12, 60), (12, 61), (12, 77), (12, 81), (13, 76), (13, 82),
                    (14, 77), (14, 81), (15, 78), (15, 79), (15, 80),
                    (23, 76), (23, 77), (24, 77), (25, 74), (25, 75), (25, 76), (26, 74)
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

    def place_template(self, template, start_row, start_column):
        rows, cols = self.world.shape
        for col, row in template:
            fila = self.camera_y + start_row + row
            columna = self.camera_x + start_column + col
            if 0 <= fila < rows and 0 <= columna < cols:
                self.world[fila, columna] = 1
        return self.view()
