import pygame
import sys
import os
import random
import yaml
import pandas as pd
import time
import math

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


def draw_redo_and_next_buttons(screen, WIN_WIDTH, WIN_HEIGHT, font, spacing=20):
    """
    Desenha os botões 'Adivinhar' e 'Próximo' lado a lado, centralizados horizontalmente.
    spacing: distância entre os botões
    """
    text_guess = font.render("Refazer", True, (255, 255, 255))
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
    rect_redo = pygame.Rect(start_x, y, width_guess, button_height)

    next_x = start_x + width_guess + spacing
    hover_next = next_x <= mouse_x <= next_x + width_next and y <= mouse_y <= y + button_height
    color_next = (60, 140, 255) if hover_next else (40, 100, 200)
    pygame.draw.rect(screen, color_next, (next_x, y, width_next, button_height), border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255), (next_x, y, width_next, button_height), 2, border_radius=10)
    screen.blit(text_next, (next_x + padding_x, y + padding_y))
    rect_next = pygame.Rect(next_x, y, width_next, button_height)

    return rect_redo, rect_next


def get_radius(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def run(screen, main_original, map_original, font, clock, choosen_image):
    WIN_WIDTH, WIN_HEIGHT = screen.get_size()
    showing_main = True
    camera_y = 0
    scroll_speed = 20
    image_position = {
        choosen_image: {
            "x": 0,
            "y": 0,
            "radius": 0
        }
    }
    
    redo_button = False
    
    next_button = None
    show_next_button = True
    
    end = False

    running = True
    positions_done = 0
    
    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.VIDEORESIZE:
                WIN_WIDTH, WIN_HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Pressionar primeira vez -> posicionar imagem
                # Pressionar segundaprimeira vez -> definir raio
                
                # Se clicar no mini mapa → troca as imagens
                if mini_x <= mouse_x <= mini_x + mini_width and mini_y <= mouse_y <= mini_y + mini_height and not end:
                    showing_main = not showing_main
                    camera_y = 0
                    image_position = None
                    show_positionate_button = False

                # Se clicar no botão “Posicionar”
                elif redo_button and redo_button.collidepoint(mouse_x, mouse_y) and image_position:
                    positions_done = 0
                    image_position = {
                        choosen_image: {
                            "x": 0,
                            "y": 0,
                            "radius": 0
                        }
                    }
                  
                # Se clicar no botão “Refazer”  
                elif positions_done >= 2 and next_button and next_button.collidepoint(mouse_x, mouse_y):
                    print("➡️ Botão 'Próximo' clicado!")
                    return image_position

                elif not end and positions_done < 2:
                    if positions_done == 0:
                        print("➡️ Posicionando imagem...", positions_done, mouse_x, mouse_y)
                        positions_done += 1
                        image_position = {
                            choosen_image: {
                                "x": mouse_x,
                                "y": mouse_y + camera_y,
                                "radius": 0
                            }
                        }
                        
                    elif positions_done == 1: 
                        print("➡️ Definindo raio...", positions_done, mouse_x, mouse_y)
                        image_position[choosen_image]["radius"] = get_radius(
                            mouse_x, mouse_y + camera_y,
                            image_position[choosen_image]["x"],
                            image_position[choosen_image]["y"]
                        )
                        positions_done += 1
        
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
        
        if positions_done >= 1 and image_position:
            center_x_img = image_position[choosen_image]["x"]
            center_y_img = image_position[choosen_image]["y"]
            
            center_y_screen = center_y_img - camera_y
            
            mouse_y_img = mouse_y + camera_y
            
            radius = get_radius(
                mouse_x, mouse_y_img,  
                center_x_img, center_y_img 
            ) if not image_position[choosen_image]["radius"] else image_position[choosen_image]["radius"]
            
            pygame.draw.circle(
                screen, 
                (255, 0, 0),  
                (int(center_x_img), int(center_y_screen)), 
                int(radius),
                2  
            )

        redo_button, next_button = draw_redo_and_next_buttons(screen, WIN_WIDTH, WIN_HEIGHT, font)
            
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


def set_yaml_data(yaml_path, yaml_data):
    with open(yaml_path, 'w') as file:
        yaml.dump(yaml_data, file)
        
        
def get_yaml_data(yaml_path):
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)
    return data


def choose_image(yaml_path, done_images):
    img_path = os.path.join("assets", "guessing")
    images = [img for img in os.listdir(img_path) if img not in done_images]

    chosen_image = random.choice(images)
    
    return chosen_image
  
def main():
    MAP_PATH = "assets/main/imagem_final.png"
    YAML_PATH = "assets/main/img_description.yml"
    WIN_WIDTH, WIN_HEIGHT = 1080, 720
    yaml_data = get_yaml_data(YAML_PATH)
    done_images = [yaml_data.keys()]
    
    while True:
        screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Gerando dados das imagens")
        
        choosen_image = choose_image(YAML_PATH, done_images)

        if not choosen_image:
            print("Não há mais imagens para processar.")
            break

        done_images.append(choosen_image)

        main_original = pygame.image.load(os.path.join("assets", "guessing", choosen_image)).convert()
        map_original = pygame.image.load(MAP_PATH).convert()

        font = pygame.font.SysFont("Arial", 32, bold=True)
        clock = pygame.time.Clock()

        yaml_data.update(run(screen, main_original, map_original, font, clock, choosen_image))
        set_yaml_data(YAML_PATH, yaml_data)
        
    pygame.quit()


if __name__ == "__main__":
    main()
