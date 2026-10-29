import pygame as game
from engine import GameEngine
from interface import UserInterface

def main():
    game.init()
    engine = GameEngine()
    ui = UserInterface(engine)
    clock = game.time.Clock()
    running = True
    playing = False
    panning = False
    pan_anchor = (0, 0, 0, 0)

    while running:
        previous_state = ui.actual_state

        for event in game.event.get():
            if event.type == game.QUIT:
                running = False

            if event.type == game.VIDEORESIZE:
                ui.width, ui.height = event.w, event.h
                ui.init_ui()
                continue

            mouse = game.mouse.get_pos()

            if ui.actual_state == ui.MENU_STATE:
                if event.type == game.KEYDOWN and event.key == game.K_ESCAPE:
                    running = False

                if event.type == game.MOUSEBUTTONDOWN and event.button == 1:
                    if ui.start_btn.collidepoint(mouse):
                        ui.button_sound.play()
                        ui.actual_state = ui.GAME_STATE
                        engine.clear_game_state()
                        game.mixer.music.stop()
                        playing = False

                    elif ui.template_btn.collidepoint(mouse):
                        ui.button_sound.play()
                        ui.selected_template_index = None
                        ui.actual_state = ui.TEMPLATES_STATE

                    elif ui.options_btn.collidepoint(mouse):
                        ui.button_sound.play()
                        ui.actual_state = ui.OPTIONS_STATE

                    elif ui.exit_btn.collidepoint(mouse):
                        running = False

            elif ui.actual_state == ui.TEMPLATES_STATE:
                if event.type == game.KEYDOWN and event.key == game.K_ESCAPE:
                    ui.play_menu_music()
                    ui.actual_state = ui.MENU_STATE

                if event.type == game.MOUSEBUTTONDOWN and event.button == 1:
                    template_catalog = engine.create_template_catalog()
                    for index, card_rect in enumerate(ui.template_cards):
                        if card_rect.collidepoint(mouse):
                            ui.button_sound.play()
                            ui.selected_template_index = index
                            engine.clear_game_state()
                            engine.place_template(template_catalog[index]["template"], 10, 10)
                            ui.actual_state = ui.GAME_STATE
                            playing = False
                            game.mixer.music.stop()
                            break

            elif ui.actual_state == ui.OPTIONS_STATE:
                if event.type == game.KEYDOWN and event.key == game.K_ESCAPE:
                    ui.play_menu_music()
                    ui.actual_state = ui.MENU_STATE

                if event.type == game.MOUSEBUTTONDOWN and event.button == 1:
                    if ui.volume_slider_rect and ui.volume_slider_rect.collidepoint(mouse):
                        ui.volume_dragging = True
                        ui.volume_value = ui.get_slider_value_from_position(mouse[0], ui.volume_slider_rect, 0, 100)
                        ui.apply_volume(ui.volume_value)
                    elif ui.fps_slider_rect and ui.fps_slider_rect.collidepoint(mouse):
                        ui.fps_dragging = True
                        ui.fps_value = ui.get_slider_value_from_position(mouse[0], ui.fps_slider_rect, 10, 120)

                if event.type == game.MOUSEBUTTONUP and event.button == 1:
                    ui.volume_dragging = False
                    ui.fps_dragging = False

                if event.type == game.MOUSEMOTION:
                    if ui.volume_dragging and ui.volume_slider_rect:
                        ui.volume_value = ui.get_slider_value_from_position(mouse[0], ui.volume_slider_rect, 0, 100)
                        ui.apply_volume(ui.volume_value)
                    elif ui.fps_dragging and ui.fps_slider_rect:
                        ui.fps_value = ui.get_slider_value_from_position(mouse[0], ui.fps_slider_rect, 10, 120)

            elif ui.actual_state == ui.GAME_STATE:
                if event.type == game.MOUSEWHEEL:
                    engine.set_cell_size(engine.cell_size + (1 if event.y > 0 else -1))

                if event.type == game.KEYDOWN:
                    if event.key == game.K_SPACE:
                        playing = not playing
                        clock.tick(100)
                        if playing:
                            ui.play_game_music()
                        else:
                            game.mixer.music.stop()

                    elif event.key == game.K_ESCAPE:
                        panning = False
                        ui.play_menu_music()
                        ui.actual_state = ui.MENU_STATE
                    elif event.key in (game.K_PLUS, game.K_EQUALS, game.K_KP_PLUS):
                        engine.set_cell_size(engine.cell_size + 1)
                    elif event.key in (game.K_MINUS, game.K_KP_MINUS):
                        engine.set_cell_size(engine.cell_size - 1)

                if event.type == game.MOUSEBUTTONDOWN and event.button == 1:
                    engine.create_life_by_click(mouse[0], mouse[1])

                # Click derecho: agarra el mundo y lo arrastra.
                if event.type == game.MOUSEBUTTONDOWN and event.button == 3:
                    panning = True
                    pan_anchor = (mouse[0], mouse[1], engine.camera_x, engine.camera_y)
                elif event.type == game.MOUSEBUTTONUP and event.button == 3:
                    panning = False
                elif event.type == game.MOUSEMOTION and panning:
                    dx = (mouse[0] - pan_anchor[0]) // engine.cell_size
                    dy = (mouse[1] - pan_anchor[1]) // engine.cell_size
                    engine.set_camera(pan_anchor[2] - dx, pan_anchor[3] - dy)

        if previous_state == ui.GAME_STATE and ui.actual_state != ui.GAME_STATE:
            engine.clear_game_state()

        if ui.actual_state == ui.GAME_STATE and game.mouse.get_pressed()[0]:
            mouse = game.mouse.get_pos()
            engine.create_life_by_click(mouse[0], mouse[1])

        # Si se suelta el boton derecho fuera de la ventana, cortar el arrastre.
        if panning and not game.mouse.get_pressed()[2]:
            panning = False

        if ui.actual_state == ui.GAME_STATE and playing:
            engine.update_grid()

        if ui.actual_state == ui.MENU_STATE:
            ui.show_menu()
        elif ui.actual_state == ui.TEMPLATES_STATE:
            ui.show_templates()
        elif ui.actual_state == ui.OPTIONS_STATE:
            ui.show_options()
        elif ui.actual_state == ui.GAME_STATE:
            ui.draw_grid(engine.view(), game.time.get_ticks())

        game.display.flip()
        if ui.actual_state == ui.GAME_STATE and playing:
            clock.tick(ui.fps_value)
        else:
            clock.tick(50)

    game.quit()

if __name__ == "__main__":
    main()
