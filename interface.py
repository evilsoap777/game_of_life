import pygame as game
import pygame.surfarray

class UserInterface:
    def __init__(self, engine, fullscreen=True, default_width=1366, default_height=768):
        self.engine = engine
        self.fullscreen = fullscreen
        self.width = default_width
        self.height = default_height
        self.screen = None

        # Colors & Constants
        self.COLOR_BG = (10, 10, 15)
        self.COLOR_GRID = (30, 30, 40)
        self.COLOR_DIE = (180, 50, 50)
        self.COLOR_ALIVE = (0, 255, 130)

        self.MENU_STATE = "menu"
        self.GAME_STATE = "game"
        self.OPTIONS_STATE = "options"
        self.TEMPLATES_STATE = "templates"
        self.actual_state = self.MENU_STATE

        # UI Elements & State
        self.start_btn = None
        self.template_btn = None
        self.options_btn = None
        self.exit_btn = None
        self.btn_font = None
        self.menu_frames = []
        self.menu_bg = []
        self.frame_actual = 0
        self.tiempo_ultimo_frame = 0
        self.selected_template_index = None
        self.template_cards = []
        self.template_image_cache = {}
        self.volume_value = 70
        self.fps_value = 50
        self.volume_slider_rect = None
        self.fps_slider_rect = None
        self.volume_dragging = False
        self.fps_dragging = False

        # Caches de render
        self._grid_surface = None
        self._overlay_surface = None
        self._overlay_key = None

        # Audio & Assets
        game.font.init()
        game.mixer.init()
        self.button_sound = game.mixer.Sound("assets/sounds/button_sound.wav")
        self.menu_music = "assets/sounds/computronium.mp3"
        self.game_music = "assets/sounds/the_world.mp3"

        self.init_display()
        self.play_menu_music()
        self.menu_frames = game.image.load_animation("assets/images/game-of-life-loop.gif")
        game.display.set_caption("Game of life")
        self.init_ui()

    def init_display(self):
        if self.fullscreen:
            info = game.display.Info()
            self.width = info.current_w
            self.height = info.current_h
            self.screen = game.display.set_mode((self.width, self.height), game.FULLSCREEN)
        else:
            self.screen = game.display.set_mode((self.width, self.height), game.RESIZABLE)
        self.engine.width = self.width
        self.engine.height = self.height

    def init_ui(self):
        button_width = min(360, max(240, self.width // 4))
        button_height = 48
        button_gap = 72

        quadrant_center_x = self.width // 4
        quadrant_center_y = self.height // 2 + self.height // 4
        total_group_height = (button_height * 4) + (button_gap * 3)

        button_x = int(quadrant_center_x - button_width // 2)
        button_y_start = int(quadrant_center_y - total_group_height // 2)

        self.start_btn = game.Rect(button_x, button_y_start, button_width, button_height)
        self.template_btn = game.Rect(button_x, button_y_start + button_gap, button_width, button_height)
        self.options_btn = game.Rect(button_x, button_y_start + button_gap * 2, button_width, button_height)
        self.exit_btn = game.Rect(button_x, button_y_start + button_gap * 3, button_width, button_height)

        self.btn_font = game.font.Font("assets/fonts/Corpta.otf", max(18, min(28, self.width // 55)))

        slider_width = min(620, self.width - 260)
        slider_x = (self.width - slider_width) // 2
        self.volume_slider_rect = game.Rect(slider_x, self.height // 2 - 80, slider_width, 88)
        self.fps_slider_rect = game.Rect(slider_x, self.height // 2 + 40, slider_width, 88)

        if self.menu_frames:
            self.menu_bg = [
                (game.transform.scale(img, (self.width, self.height)), delay)
                for img, delay in self.menu_frames
            ]
        else:
            self.menu_bg = []

        self.template_cards = []
        columns = 3
        rows = 2
        card_width = min(360, max(260, (self.width - 140) // columns))
        card_height = 180
        card_gap_x = 28
        card_gap_y = 28
        total_grid_width = (card_width * columns) + (card_gap_x * (columns - 1))
        total_grid_height = (card_height * rows) + (card_gap_y * (rows - 1))
        start_x = (self.width - total_grid_width) // 2
        start_y = max(140, (self.height - total_grid_height) // 2 - 20)

        template_catalog = self.engine.create_template_catalog()
        for index in range(len(template_catalog)):
            col = index % columns
            row = index // columns
            x = start_x + col * (card_width + card_gap_x)
            y = start_y + row * (card_height + card_gap_y)
            self.template_cards.append(game.Rect(x, y, card_width, card_height))

        self.frame_actual = 0
        self.tiempo_ultimo_frame = game.time.get_ticks()
        self.engine.resize_viewport(self.width, self.height)

    def play_menu_music(self):
        game.mixer.music.stop()
        game.mixer.music.load(self.menu_music)
        game.mixer.music.play(-1)

    def play_game_music(self):
        game.mixer.music.stop()
        game.mixer.music.load(self.game_music)
        game.mixer.music.play(-1)

    def apply_volume(self, new_volume):
        if game.mixer.get_init():
            normalized = new_volume / 100.0
            game.mixer.music.set_volume(normalized)
            self.button_sound.set_volume(normalized)

    def get_neon_alive_color(self, ticks):
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

    def draw_animated_background(self):
        if self.menu_bg:
            imagen_frame, delay_frame = self.menu_bg[self.frame_actual]
            self.screen.blit(imagen_frame, (0, 0))

            tiempo_actual = game.time.get_ticks()
            if tiempo_actual - self.tiempo_ultimo_frame >= delay_frame:
                self.frame_actual = (self.frame_actual + 1) % len(self.menu_bg)
                self.tiempo_ultimo_frame = tiempo_actual
        else:
            self.screen.fill(self.COLOR_BG)

    def draw_button(self, button_rect, text):
        COLOR_BOTON = (30, 30, 45)
        game.draw.rect(self.screen, COLOR_BOTON, button_rect)
        text_surface = self.btn_font.render(text, True, (255, 255, 255))
        self.screen.blit(text_surface, (
            button_rect.x + (button_rect.width - text_surface.get_width()) // 2,
            button_rect.y + (button_rect.height - text_surface.get_height()) // 2
        ))

    def show_menu(self):
        self.draw_animated_background()
        self.draw_button(self.start_btn, "Iniciar Simulacion")
        self.draw_button(self.template_btn, "Cargar plantilla")
        self.draw_button(self.options_btn, "Opciones")
        self.draw_button(self.exit_btn, "Salir")

    def get_template_preview_surface(self, image_name, size):
        if not image_name:
            return None

        if image_name not in self.template_image_cache:
            try:
                image_surface = game.image.load(f"assets/images/{image_name}")
                self.template_image_cache[image_name] = game.transform.scale(image_surface, size)
            except Exception:
                self.template_image_cache[image_name] = None

        return self.template_image_cache.get(image_name)

    def show_templates(self):
        self.draw_animated_background()
        template_catalog = self.engine.create_template_catalog()

        for index, card_rect in enumerate(self.template_cards):
            card_color = (35, 35, 45)
            if self.selected_template_index == index:
                card_color = (55, 85, 70)

            game.draw.rect(self.screen, card_color, card_rect)
            game.draw.rect(self.screen, (120, 120, 140), card_rect, 1)

            preview_rect = game.Rect(card_rect.x + 12, card_rect.y + 12, 100, card_rect.height - 24)
            preview_surface = self.get_template_preview_surface(template_catalog[index]["image"], (preview_rect.width, preview_rect.height))
            if preview_surface is not None:
                self.screen.blit(preview_surface, preview_rect)
            else:
                game.draw.rect(self.screen, (50, 70, 120), preview_rect)
                game.draw.rect(self.screen, (150, 170, 210), preview_rect, 1)
                preview_text = game.font.Font(None, 18).render("Imagen", True, (220, 220, 220))
                self.screen.blit(preview_text, (preview_rect.x + 10, preview_rect.y + 34))

            text_area_width = card_rect.width - preview_rect.width - 36
            text_x = card_rect.x + preview_rect.width + 18
            text_y = card_rect.y + 20

            title_font = game.font.Font("assets/fonts/Corpta.otf", 24)
            title_surface = title_font.render(template_catalog[index]["title"], True, (255, 255, 255))
            self.screen.blit(title_surface, (text_x, text_y))

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
                self.screen.blit(desc_surface, (text_x, desc_y))
                desc_y += 20

    def draw_stats(self):
        stats_font = game.font.Font(None, 24)
        text = f"Creadas: {self.engine.created_cells}  Muertas: {self.engine.dead_cells}"
        text_surface = stats_font.render(text, True, (255, 255, 255))
        panel_rect = game.Rect(self.width - text_surface.get_width() - 20, 20, text_surface.get_width() + 16, text_surface.get_height() + 10)
        game.draw.rect(self.screen, (20, 20, 30), panel_rect)
        game.draw.rect(self.screen, (90, 90, 110), panel_rect, 1)
        self.screen.blit(text_surface, (panel_rect.x + 8, panel_rect.y + 5))

    def draw_grid(self, grid, ticks):
        rows, cols = grid.shape
        if rows == 0 or cols == 0:
            self.screen.fill(self.COLOR_BG)
            self.draw_stats()
            return

        color_alive = self.get_neon_alive_color(ticks)

        # Superficie indexada de 8 bits: 1 byte por celda en vez de 3 y el
        # escalado final lo hace SDL sobre indices, no sobre RGB.
        grid_surface = self._grid_surface
        if grid_surface is None or grid_surface.get_size() != (cols, rows):
            grid_surface = game.Surface((cols, rows), depth=8)
            self._grid_surface = grid_surface
        grid_surface.set_palette([self.COLOR_BG, color_alive] + [(0, 0, 0)] * 254)
        game.surfarray.blit_array(grid_surface, grid.T)

        scaled_surf = game.transform.scale(grid_surface, (self.width, self.height))
        self.screen.blit(scaled_surf, (0, 0))

        if self.engine.cell_size >= 6:
            overlay = self.get_grid_overlay(self.engine.cell_size)
            self.screen.blit(overlay, (0, 0), special_flags=game.BLEND_ADD)

        self.draw_stats()

    def get_grid_overlay(self, cell_size):
        key = (cell_size, self.width, self.height)
        if self._overlay_surface is None or self._overlay_key != key:
            overlay = game.Surface((self.width, self.height))
            overlay.fill((0, 0, 0))
            for x in range(0, self.width, cell_size):
                game.draw.line(overlay, self.COLOR_GRID, (x, 0), (x, self.height))
            for y in range(0, self.height, cell_size):
                game.draw.line(overlay, self.COLOR_GRID, (0, y), (self.width, y))
            self._overlay_surface = overlay
            self._overlay_key = key
        return self._overlay_surface

    def clamp(self, value, min_value, max_value):
        return max(min_value, min(max_value, value))

    def get_slider_value_from_position(self, x, slider_rect, min_value, max_value):
        relative_x = self.clamp(x - slider_rect.x, 0, slider_rect.width)
        ratio = relative_x / slider_rect.width
        return int(round(min_value + ratio * (max_value - min_value)))

    def draw_slider(self, label, value, min_value, max_value, rect):
        label_surface = self.btn_font.render(label, True, (255, 255, 255))
        label_bg_rect = game.Rect(rect.x - 10, rect.y - 8, label_surface.get_width() + 20, label_surface.get_height() + 14)
        game.draw.rect(self.screen, (0, 0, 0), label_bg_rect)
        game.draw.rect(self.screen, (90, 90, 110), label_bg_rect, 1)
        self.screen.blit(label_surface, (rect.x, rect.y))

        track_rect = game.Rect(rect.x, rect.y + 42, rect.width, 10)
        game.draw.rect(self.screen, (60, 60, 80), track_rect)

        fill_width = int((value - min_value) / (max_value - min_value) * track_rect.width)
        fill_rect = game.Rect(track_rect.x, track_rect.y, fill_width, track_rect.height)
        game.draw.rect(self.screen, (70, 190, 170), fill_rect)

        handle_center = (track_rect.x + fill_width, track_rect.y + track_rect.height // 2)
        game.draw.circle(self.screen, (230, 230, 230), handle_center, 12)
        game.draw.circle(self.screen, (35, 35, 55), handle_center, 7)

        return track_rect

    def show_options(self):
        self.draw_animated_background()

        slider_width = min(620, self.width - 260)
        slider_x = (self.width - slider_width) // 2
        self.volume_slider_rect = game.Rect(slider_x, self.height // 2 - 80, slider_width, 88)
        self.fps_slider_rect = game.Rect(slider_x, self.height // 2 + 40, slider_width, 88)

        self.draw_slider("Volumen", self.volume_value, 0, 100, self.volume_slider_rect)
        self.draw_slider("FPS", self.fps_value, 10, 120, self.fps_slider_rect)
