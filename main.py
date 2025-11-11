import pygame
import sys
import os
import random
import yaml
import pandas as pd
import time

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
    score = 0.0

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
                    score = choosen_image.get_score((pin_position['x'], pin_position['y']))
                    choosen_image.draw_line(camera_y=camera_y)
                    choosen_image.draw_circle(camera_y=camera_y)
                    
                    
                    show_guess_button = False
                    guess_button_rect = None
                    end = True
                    
                elif show_next_button and next_button_rect and next_button_rect.collidepoint(mouse_x, mouse_y) and end:
                    return score

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
                choosen_image.draw_line(camera_y=camera_y, font=font)

            guess_button_rect, next_button_rect = draw_guess_and_next_buttons(screen, WIN_WIDTH, WIN_HEIGHT, font)
            
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()


def get_yaml_data(yaml_path):
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)
    return data


def choose_image(yaml_path, done_images):
    image_data = get_yaml_data(yaml_path)
    images = [img for img in os.listdir("assets/guessing") if img not in done_images and img in image_data.keys()]
    
    if images:
        chosen_image = random.choice(images)
        image_data = image_data[chosen_image]
        
        if image_data:
            return Place(
                    path=os.path.join("assets", "guessing", chosen_image), 
                    position=(image_data['x'], image_data['y']), 
                    radius=image_data['radius'], 
                    name=chosen_image
                )
    print(f"Nenhuma imagem válida encontrada. Verifique o arquivo YAML.")
    return None
  

def draw_title(screen, text, font, text_color, border_color, x, y, border_thickness):
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)


def draw_text_with_border(screen, text, font, text_color, border_color, x, y, border_thickness):
    """Desenha texto com uma borda simples."""
    text_surface = font.render(text, True, text_color)
    border_surface = font.render(text, True, border_color)
    
    text_rect = text_surface.get_rect(center=(x, y))

    # Desenha a borda em 8 direções
    screen.blit(border_surface, text_rect.move(-border_thickness, -border_thickness))
    screen.blit(border_surface, text_rect.move(0, -border_thickness))
    screen.blit(border_surface, text_rect.move(border_thickness, -border_thickness))
    screen.blit(border_surface, text_rect.move(-border_thickness, 0))
    screen.blit(border_surface, text_rect.move(border_thickness, 0))
    screen.blit(border_surface, text_rect.move(-border_thickness, border_thickness))
    screen.blit(border_surface, text_rect.move(0, border_thickness))
    screen.blit(border_surface, text_rect.move(border_thickness, border_thickness))

    # Desenha o texto principal por cima
    screen.blit(text_surface, text_rect)


def start_screen(screen, WIN_WIDTH, WIN_HEIGHT, font, background_image_path):
    """Mostra a tela inicial com uma imagem de fundo e botão 'Começar'."""
    
    title_font = pygame.font.SysFont("Arial", 64, bold=True)
    input_font = pygame.font.SysFont("Arial", 32)
    clock = pygame.time.Clock()

    user_name = ""
    active_input = False
    
    # --- MUDANÇA 1: Carrega a imagem ORIGINAL ---
    background_original = pygame.image.load(background_image_path).convert()
    # --- MUDANÇA 2: Cria a primeira versão escalada ---
    background_scaled = pygame.transform.smoothscale(background_original, (WIN_WIDTH, WIN_HEIGHT))

    # --- MUDANÇA 3: Remove o cálculo do 'input_rect' daqui ---
    # input_rect = pygame.Rect(WIN_WIDTH//2 - 200, WIN_HEIGHT//2 - 30, 400, 50)
    
    running = True
    while running:
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # --- MUDANÇA 4: Recalcula o 'input_rect' DENTRO do loop ---
        input_rect = pygame.Rect(WIN_WIDTH//2 - 200, WIN_HEIGHT//2 - 30, 400, 50)
        
        # O cálculo do botão já estava dentro do loop, o que é ótimo
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

            # --- MUDANÇA 5: Adiciona o handler para VIDEORESIZE ---
            elif event.type == pygame.VIDEORESIZE:
                WIN_WIDTH, WIN_HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.RESIZABLE)
                # Re-escala a imagem de fundo original para o novo tamanho
                background_scaled = pygame.transform.smoothscale(background_original, (WIN_WIDTH, WIN_HEIGHT))
            # --- Fim da MUDANÇA 5 ---

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button_rect.collidepoint(event.pos) and user_name.strip() != "":
                    return user_name

                if input_rect.collidepoint(event.pos):
                    active_input = True
                else:
                    active_input = False

            elif event.type == pygame.KEYDOWN and active_input:
                if event.key == pygame.K_BACKSPACE:
                    user_name = user_name[:-1]

                elif event.key == pygame.K_RETURN:
                    if user_name.strip() != "":
                        return user_name

                elif event.unicode.isprintable(): 
                    # Verifica se o novo texto caberá
                    current_width = input_font.render(user_name, True, (0,0,0)).get_width()
                    if current_width < input_rect.width - 20: # -20 de padding
                        user_name += event.unicode

        # --- MUDANÇA 6: Desenha a imagem 'background_scaled' ---
        screen.blit(background_scaled, (0, 0))
        
        # O título já usa as variáveis dinâmicas, está correto
        draw_title(
            screen,
            "UDESC vista de cima",
            title_font,
            text_color=(255, 255, 255),
            border_color=(0, 255, 0), # Mudei para verde, como no seu código
            x=WIN_WIDTH // 2,
            y=WIN_HEIGHT // 3,
            border_thickness=2 # 10 é muito, 2 fica melhor
        )
        
        # --- DESENHO DO INPUT BOX ---
        # (Seu código original estava desenhando o texto 2x, eu limpei)
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

        # --- DESENHO DO BOTÃO ---
        hover = button_rect.collidepoint(mouse_x, mouse_y)
        color = (60, 140, 255) if hover else (40, 100, 200)

        pygame.draw.rect(screen, color, button_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), button_rect, 2, border_radius=10)
        
        text_x_pos = button_rect.x + (button_rect.width - button_text.get_width()) // 2
        text_y_pos = button_rect.y + (button_rect.height - button_text.get_height()) // 2
        screen.blit(button_text, (text_x_pos, text_y_pos))
        
        pygame.display.flip()
        clock.tick(30)        
  
  
def leader_board(screen, font, clock, background_image_path):
    """Exibe a tela de leaderboard com os 10 melhores scores."""
    WIN_WIDTH, WIN_HEIGHT = screen.get_size()
    
    # Carrega e escala o fundo
    try:
        background = pygame.image.load(background_image_path).convert()
        background = pygame.transform.smoothscale(background, (WIN_WIDTH, WIN_HEIGHT))
    except pygame.error:
        # Fallback para cor sólida se a imagem falhar
        background = pygame.Surface((WIN_WIDTH, WIN_HEIGHT))
        background.fill((10, 20, 40))

    # Define fontes
    title_font = pygame.font.SysFont("Arial", 64, bold=True)
    header_font = pygame.font.SysFont("Arial", 36, bold=True)
    score_font = pygame.font.SysFont("Arial", 32)

    # Carrega e processa os dados
    try:
        df = pd.read_csv(os.path.join("assets", "scores.csv"))
        if df.empty:
            raise FileNotFoundError # Trata como se não houvesse dados
            
        # Garante que os tipos estão corretos
        df['points'] = pd.to_numeric(df['points'])
        df['time'] = pd.to_numeric(df['time'])

        # 1. Ordena por pontos (maior primeiro) e tempo (menor primeiro)
        df_sorted = df.sort_values(by=['points', 'time'], ascending=[False, True])
        
        # 2. Pega o melhor score de cada jogador
        best_scores = df_sorted.drop_duplicates(subset='name', keep='first')
        
        # 3. Pega os 10 melhores
        top_10 = best_scores.head(10)
        
    except (FileNotFoundError, pd.errors.EmptyDataError):
        top_10 = pd.DataFrame(columns=["name", "points", "time"]) # DataFrame vazio

    running = True
    while running:
        mouse_x, mouse_y = pygame.mouse.get_pos()

        button_text = font.render("Fechar", True, (255, 255, 255))
        padding_x, padding_y = 30, 15
        button_width = button_text.get_width() + padding_x * 2
        button_height = button_text.get_height() + padding_y * 2
        button_x = WIN_WIDTH // 2 - button_width // 2
        button_y = WIN_HEIGHT - button_height - 30 # Y-pos do topo do botão
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # --- Loop de Eventos ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.VIDEORESIZE:
                WIN_WIDTH, WIN_HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.RESIZABLE)
                try:
                    background = pygame.transform.smoothscale(background.copy(), (WIN_WIDTH, WIN_HEIGHT))
                except: # Lida com o fallback
                    background = pygame.Surface((WIN_WIDTH, WIN_HEIGHT))
                    background.fill((10, 20, 40))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button_rect.collidepoint(event.pos):
                    running = False # Sai do loop do leaderboard

        screen.blit(background, (0, 0))
        
        panel_margin_x = 80
        panel_y_top = 50
        
        # Calcula as dimensões
        panel_x = panel_margin_x
        panel_y = panel_y_top
        panel_width = WIN_WIDTH - (panel_margin_x * 2)
        panel_height = (button_y - 20) - panel_y_top # Termina 20px acima do botão
        
        overlay = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        
        overlay.fill((0, 0, 0, 180))
        
        pygame.draw.rect(overlay, (255, 255, 255, 40), overlay.get_rect(), 2, border_radius=10)

        # Desenha o painel na tela principal
        screen.blit(overlay, (panel_x, panel_y))
        
        draw_text_with_border(
            screen, "Leaderboard", title_font, 
            (255, 255, 255), (0, 0, 0), 
            WIN_WIDTH // 2, 80, 2
        )

        # Cabeçalhos (Ajuste as posições X se necessário para caber no painel)
        padding_total = panel_x + 50 # padding de 50px dentro do painel
        col_rank = padding_total
        col_name = padding_total + 100
        col_points = panel_width - 250 # Alinha à direita
        col_time = panel_width - 80   # Alinha à direita
        
        y_header = 180
        screen.blit(header_font.render("Rank", True, (255, 215, 0)), (col_rank, y_header))
        screen.blit(header_font.render("Nome", True, (255, 215, 0)), (col_name, y_header))
        screen.blit(header_font.render("Pontos", True, (255, 215, 0)), (col_points, y_header))
        screen.blit(header_font.render("Tempo", True, (255, 215, 0)), (col_time, y_header))
        
        pygame.draw.line(screen, (255, 215, 0), 
                         (col_rank, y_header + 40), 
                         (col_time + header_font.size("Tempo")[0], y_header + 40), 2)

        # Scores
        y_offset = y_header + 70
        if top_10.empty:
            no_data_text = score_font.render("Nenhuma pontuação registrada ainda.", True, (200, 200, 200))
            screen.blit(no_data_text, (WIN_WIDTH // 2 - no_data_text.get_width() // 2, y_offset + 50))
            
        for i, row in enumerate(top_10.itertuples()):
            rank_str = f"{i+1}."
            name_str = str(row.name).title() # Capitaliza o nome
            points_str = f"{int(row.points)}"
            time_str = f"{row.time:.2f}s"

            screen.blit(score_font.render(rank_str, True, (255, 255, 255)), (col_rank, y_offset))
            screen.blit(score_font.render(name_str, True, (255, 255, 255)), (col_name, y_offset))
            screen.blit(score_font.render(points_str, True, (255, 255, 255)), (col_points, y_offset))
            screen.blit(score_font.render(time_str, True, (255, 255, 255)), (col_time, y_offset))
            y_offset += 40

        # Botão Fechar (agora desenhado por último)
        hover = button_rect.collidepoint(mouse_x, mouse_y)
        color = (200, 0, 0) if hover else (150, 0, 0) # Vermelho para fechar

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
    background_image_path = os.path.join("assets", "main", "main.png")
    
    clock = pygame.time.Clock() 

    user_name = start_screen(screen, WIN_WIDTH, WIN_HEIGHT, font, background_image_path)
    user_score = 0
    
    done_images = []
    
    try:
        df = pd.read_csv(os.path.join("assets", "scores.csv"))
    except (FileNotFoundError, pd.errors.EmptyDataError): # Adicionado EmptyDataError
        df = pd.DataFrame(columns=["name", "points", "time", "date"])
        
    
    time_start = time.time()
    for i in range(3): 

        MAP_PATH = "assets/main/imagem_final.png"
        YAML_PATH = "assets/main/img_description.yml"
        PIN_PATH = "assets/main/pin.png"
        
        choosen_image = choose_image(YAML_PATH, done_images)

        if not choosen_image:
            print("Não há mais imagens para jogar.")
            break # Sai do loop se não houver mais imagens

        done_images.append(choosen_image.name)

        main_original = pygame.image.load(choosen_image.path).convert()
        map_original = pygame.image.load(MAP_PATH).convert()
        pin_image = pygame.image.load(PIN_PATH).convert_alpha()

        # font = pygame.font.SysFont("Arial", 32, bold=True) # Já definido
        # clock = pygame.time.Clock() # Já definido

        choosen_image.set_screen(screen)
        choosen_image.draw_circle()
        
        
        user_score += run(screen, main_original, map_original, pin_image, font, clock, choosen_image)
    
    end_time = time.time()
    
    new_row = {
        "name": user_name.lower(),
        "points": user_score,
        "time": end_time - time_start,
        "date": time.strftime("%Y-%m-%d %H:%M:%S") 
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
    df.to_csv(os.path.join("assets", "scores.csv"), index=False)
    
    leader_board(screen, font, clock, background_image_path)
    
    pygame.quit()


if __name__ == "__main__":
    main()
