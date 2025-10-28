import pygame
import sys
import os
import random
import yaml

from src.place import Place

pygame.init()


def crop_center(surface, target_ratio=16 / 9):
    """Corta o centro da imagem para manter a proporção desejada (ex: 16:9)."""
    w, h = surface.get_size()
    current_ratio = w / h

    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        x = (w - new_w) // 2
        rect = pygame.Rect(x, 0, new_w, h)
    else:
        new_h = int(w / target_ratio)
        y = (h - new_h) // 2
        rect = pygame.Rect(0, y, w, new_h)

    cropped = surface.subsurface(rect)
    return cropped.copy()


def draw_scene(screen, active_image, minimap_image, is_map_image, WIN_WIDTH, WIN_HEIGHT, camera_y):
    """Desenha a imagem principal, o mini mapa e retorna dados do mini mapa."""
    img_width, img_height = active_image.get_size()
    scale_factor = WIN_WIDTH / img_width
    scaled_height = int(img_height * scale_factor)
    active_scaled = pygame.transform.smoothscale(active_image, (WIN_WIDTH, scaled_height))

    camera_y = max(0, min(scaled_height - WIN_HEIGHT, camera_y))

    screen.blit(active_scaled, (0, -camera_y))

    mini_width = int(WIN_WIDTH * 0.25)
    mini_scale_factor = mini_width / minimap_image.get_width()
    mini_height = int(minimap_image.get_height() * mini_scale_factor)

    if is_map_image:
        minimap_image = crop_center(minimap_image, 16 / 9)
        mini_scale_factor = mini_width / minimap_image.get_width()
        mini_height = int(minimap_image.get_height() * mini_scale_factor)

    mini_x = WIN_WIDTH - mini_width - 10
    mini_y = WIN_HEIGHT - mini_height - 10
    mouse_x, mouse_y = pygame.mouse.get_pos()
    hover = mini_x <= mouse_x <= mini_x + mini_width and mini_y <= mouse_y <= mini_y + mini_height

    zoom = 1.1 if hover else 1.0
    zoomed_width = int(mini_width * zoom)
    zoomed_height = int(mini_height * zoom)
    zoomed_image = pygame.transform.smoothscale(minimap_image, (zoomed_width, zoomed_height))

    zoomed_x = WIN_WIDTH - zoomed_width - 10
    zoomed_y = WIN_HEIGHT - zoomed_height - 10

    screen.blit(zoomed_image, (zoomed_x, zoomed_y))

    pygame.draw.rect(screen, (255, 255, 255),
                     (zoomed_x - 2, zoomed_y - 2, zoomed_width + 4, zoomed_height + 4), 2)

    return zoomed_x, zoomed_y, zoomed_width, zoomed_height, scale_factor, scaled_height, camera_y


def draw_guess_and_next_buttons(screen, WIN_WIDTH, WIN_HEIGHT, font, spacing=20):
    """
    Desenha os botões 'Adivinhar' e 'Próximo' lado a lado, centralizados horizontalmente.
    spacing: distância entre os botões
    """
    text_guess = font.render("Adivinhar", True, (255, 255, 255))
    text_next = font.render("Próximo", True, (255, 255, 255))
    padding_x, padding_y = 30, 15

    width_guess = text_guess.get_width() + padding_x * 2
    height_guess = text_guess.get_height() + padding_y * 2

    width_next = text_next.get_width() + padding_x * 2
    height_next = text_next.get_height() + padding_y * 2

    button_height = max(height_guess, height_next)

    total_width = width_guess + spacing + width_next

    start_x = WIN_WIDTH // 2 - total_width // 2
    y = WIN_HEIGHT - button_height - 30

    mouse_x, mouse_y = pygame.mouse.get_pos()
    hover_guess = start_x <= mouse_x <= start_x + width_guess and y <= mouse_y <= y + button_height
    color_guess = (60, 140, 255) if hover_guess else (40, 100, 200)
    pygame.draw.rect(screen, color_guess, (start_x, y, width_guess, button_height), border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255), (start_x, y, width_guess, button_height), 2, border_radius=10)
    screen.blit(text_guess, (start_x + padding_x, y + padding_y))
    rect_guess = pygame.Rect(start_x, y, width_guess, button_height)

    next_x = start_x + width_guess + spacing
    hover_next = next_x <= mouse_x <= next_x + width_next and y <= mouse_y <= y + button_height
    color_next = (60, 140, 255) if hover_next else (40, 100, 200)
    pygame.draw.rect(screen, color_next, (next_x, y, width_next, button_height), border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255), (next_x, y, width_next, button_height), 2, border_radius=10)
    screen.blit(text_next, (next_x + padding_x, y + padding_y))
    rect_next = pygame.Rect(next_x, y, width_next, button_height)

    return rect_guess, rect_next


def run(screen, main_original, map_original, pin_image, font, clock, choosen_image):
    WIN_WIDTH, WIN_HEIGHT = screen.get_size()
    showing_main = True
    camera_y = 0
    scroll_speed = 20
    pin_position = None
    show_guess_button = False
    guess_button_rect = None
    next_button_rect = None
    show_next_button = True

    end = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                WIN_WIDTH, WIN_HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Se clicar no mini mapa → troca as imagens
                if mini_x <= mouse_x <= mini_x + mini_width and mini_y <= mouse_y <= mini_y + mini_height and not end:
                    showing_main = not showing_main
                    camera_y = 0
                    pin_position = None
                    show_guess_button = False

                # Se clicar no botão “Adivinhar”
                elif show_guess_button and guess_button_rect and guess_button_rect.collidepoint(mouse_x, mouse_y):
                    print("🟩 Botão 'Adivinhar' clicado!", show_guess_button)
                    score = choosen_image.get_score((pin_position['x'], pin_position['y']))
                    print(f"Pontuação obtida: {score:.4f}")
                    choosen_image.draw_line(camera_y=camera_y)
                    
                    show_guess_button = False
                    guess_button_rect = None
                    end = True
                    
                elif show_next_button and next_button_rect and next_button_rect.collidepoint(mouse_x, mouse_y) and end:
                    print("➡️ Botão 'Próximo' clicado!")
                    return  

                elif not end:
                    pin_position = {
                        "x": mouse_x,
                        "y": mouse_y + camera_y,
                        "context": "main" if showing_main else "map",
                    }
                    show_guess_button = True

        # Movimento do mouse para rolar a imagem
        mouse_y = pygame.mouse.get_pos()[1]
        if mouse_y < WIN_HEIGHT * 0.025:
            camera_y -= scroll_speed
        elif mouse_y > WIN_HEIGHT * 0.975:
            camera_y += scroll_speed

        # Seleciona imagens ativas
        if showing_main:
            active_img = main_original
            mini_img = map_original
            mini_is_map = True
        else:
            active_img = map_original
            mini_img = main_original
            mini_is_map = False

        mini_x, mini_y, mini_width, mini_height, scale_factor, scaled_height, camera_y = draw_scene(
            screen, active_img, mini_img, mini_is_map, WIN_WIDTH, WIN_HEIGHT, camera_y
        )

        # 🧷 Desenha o pin se existir
        if pin_position and pin_position["context"] == "map":
            draw_x = pin_position["x"] - 25
            draw_y = pin_position["y"] - camera_y - 50
            scaled_pin = pygame.transform.scale(pin_image, (50, 50))
            screen.blit(scaled_pin, (draw_x, draw_y))

            # Desenha o círculo e a linha apenas se estivermos vendo o mapa
            if not showing_main:
                choosen_image.draw_circle(camera_y=camera_y)
                choosen_image.draw_line(camera_y=camera_y, font=font)

            guess_button_rect, next_button_rect = draw_guess_and_next_buttons(screen, WIN_WIDTH, WIN_HEIGHT, font)
            
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()


def get_yaml_data(yaml_path, image_name):
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)
    return data['images'][image_name]


def choose_image(yaml_path, done_images):
    images = [img for img in os.listdir("assets/guessing") if img not in done_images]
    
    chosen_image = random.choice(images)
    
    image_data = get_yaml_data(yaml_path, chosen_image)
    if image_data:
        return Place(
                path=os.path.join("assets/guessing", chosen_image), 
                position=(image_data['pos_x'], image_data['pos_y']), 
                radius=image_data['radius'], 
                name=chosen_image
            )
    print(f"Nenhuma imagem válida encontrada para {chosen_image}. Verifique o arquivo YAML.")
    return None
  

def draw_text_with_border(screen, text, font, text_color, border_color, x, y, border_thickness):
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)


def start_screen(screen, WIN_WIDTH, WIN_HEIGHT, font, background_image_path):
    """Mostra a tela inicial com uma imagem de fundo e botão 'Começar'."""
    
    title_font = pygame.font.SysFont("Arial", 64, bold=True)
    input_font = pygame.font.SysFont("Arial", 32)
    clock = pygame.time.Clock()

    user_name = ""
    active_input = False
    
    background = pygame.image.load(background_image_path).convert()
    background = pygame.transform.smoothscale(background, (WIN_WIDTH, WIN_HEIGHT))

    input_rect = pygame.Rect(WIN_WIDTH//2 - 200, WIN_HEIGHT//2 - 30, 400, 50)
    
    running = True
    while running:
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        button_text = font.render("Começar", True, (255, 255, 255))
        padding_x, padding_y = 30, 15
        button_width = button_text.get_width() + padding_x * 2
        button_height = button_text.get_height() + padding_y * 2
        button_x = WIN_WIDTH // 2 - button_width // 2
        button_y = WIN_HEIGHT // 2 + 50
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button_rect.collidepoint(event.pos) and user_name.strip() != "":
                    print(f"Usuário {user_name} começou o jogo (via clique).")
                    return user_name

                if input_rect.collidepoint(event.pos):
                    active_input = True
                else:
                    active_input = False

            if event.type == pygame.KEYDOWN and active_input:
                if event.key == pygame.K_BACKSPACE:
                    user_name = user_name[:-1]

                elif event.key == pygame.K_RETURN:
                    if user_name.strip() != "":
                        print(f"Usuário {user_name} começou o jogo (via Enter).")
                        return user_name

                elif event.unicode.isprintable():  
                    if input_font.render(user_name, True, (0,0,0)).get_width() < input_rect.width - 20:
                        user_name += event.unicode

        screen.blit(background, (0, 0))
        
        draw_text_with_border(
            screen,
            "UDESC vista de cima",
            title_font,
            text_color=(255, 255, 255),
            border_color=(0, 255, 0),
            x=WIN_WIDTH // 2,
            y=WIN_HEIGHT // 3,
            border_thickness=10
        )
        
        pygame.draw.rect(screen, (0, 0, 0), input_rect, border_radius=5)
        
        input_border_color = (100, 200, 255) if active_input else (255, 255, 255)
        pygame.draw.rect(screen, (0, 0, 0), input_rect, border_radius=5)

        input_border_color = (100, 200, 255) if active_input else (255, 255, 255)
        pygame.draw.rect(screen, input_border_color, input_rect, 2, border_radius=5)

        text_y_pos = input_rect.y + (input_rect.height - input_font.get_height()) // 2

        if user_name == "":
            placeholder_surf = input_font.render("Nome Completo", True, (150, 150, 150))
            screen.blit(placeholder_surf, (input_rect.x + 10, text_y_pos))
        else:
            input_surface = input_font.render(user_name, True, (255, 255, 255))
            screen.blit(input_surface, (input_rect.x + 10, text_y_pos))

        
        input_surface = input_font.render(user_name, True, (255, 255, 255))
        text_y_pos = input_rect.y + (input_rect.height - input_surface.get_height()) // 2
        screen.blit(input_surface, (input_rect.x + 10, text_y_pos))

        hover = button_rect.collidepoint(mouse_x, mouse_y)
        color = (60, 140, 255) if hover else (40, 100, 200)

        pygame.draw.rect(screen, color, button_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), button_rect, 2, border_radius=10)
        
        text_x_pos = button_rect.x + (button_rect.width - button_text.get_width()) // 2
        text_y_pos = button_rect.y + (button_rect.height - button_text.get_height()) // 2
        screen.blit(button_text, (text_x_pos, text_y_pos))
        
        pygame.display.flip()
        clock.tick(30)
        
        
def main():
    WIN_WIDTH, WIN_HEIGHT = 1080, 720
    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("UDESC vista de cima")
    font = pygame.font.SysFont("Arial", 32, bold=True)
    background_image_path = os.path.join("assets/main", "main.png")

    start_screen(screen, WIN_WIDTH, WIN_HEIGHT, font, background_image_path)
    
    
    done_images = []
    
    for i in range(2):
        WIN_WIDTH, WIN_HEIGHT = 1080, 720
        screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("UDESC vista de cima")

        MAP_PATH = "assets/main/imagem_final.png"
        YAML_PATH = "assets/main/img_description.yml"
        PIN_PATH = "assets/main/pin.png"
        
        choosen_image = choose_image(YAML_PATH, done_images)

        if not choosen_image:
            return

        done_images.append(choosen_image.name)

        main_original = pygame.image.load(choosen_image.path).convert()
        map_original = pygame.image.load(MAP_PATH).convert()
        pin_image = pygame.image.load(PIN_PATH).convert_alpha()

        font = pygame.font.SysFont("Arial", 32, bold=True)
        clock = pygame.time.Clock()

        choosen_image.set_screen(screen)
        choosen_image.draw_circle()
        
        
        run(screen, main_original, map_original, pin_image, font, clock, choosen_image)


if __name__ == "__main__":
    main()
