import pygame

class Place:
    def __init__(self, path, name, position, radius=0):
        self.path = path
        self.name = name
        self.position = position 
        self.radius = radius
        self.guessed_position = None
        self.screen = None 
        
    def set_screen(self, screen):
        self.screen = screen

    def get_score(self, guessed_position):
        self.guessed_position = guessed_position
        distance = self.get_distance()

        max_distance = 1_000 
        if distance <= 0:
            return 100
        elif distance >= max_distance:
            return 0
        else:
            score = 100 * (1 - distance / max_distance)
            return round(score)


    def get_distance(self):
        """Calcula a distância entre o ponto real e o chute do jogador."""
        distance = ((self.position[0] - self.guessed_position[0]) ** 2 +
                    (self.position[1] - self.guessed_position[1]) ** 2) ** 0.5
        if distance < self.radius:
            return 0
        return distance - self.radius

    def draw_circle(self, camera_y=0, color=(255, 0, 0), width=2):
        """Desenha um círculo semi-transparente na posição do local real."""
        circle_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        x, y = self.position
        y_on_screen = y - camera_y

        transparent_color = (*color, 100)

        pygame.draw.circle(circle_surface, transparent_color,
                           (int(x), int(y_on_screen)), int(self.radius))

        pygame.draw.circle(circle_surface, color,
                           (int(x), int(y_on_screen)), int(self.radius), width)

        self.screen.blit(circle_surface, (0, 0))

    def draw_line(self, camera_y=0, color=(0, 255, 0), width=3, font=None):
        """Desenha uma linha do local correto até o palpite e mostra a pontuação."""
        if self.guessed_position is None:
            return

        x1, y1 = self.position
        x2, y2 = self.guessed_position

        y1 -= camera_y
        y2 -= camera_y

        pygame.draw.line(self.screen, color, (int(x1), int(y1)), (int(x2), int(y2)), width)

        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        score = self.get_score(self.guessed_position)
        text_value = f"{score:.3f}"

        if font is None:
            font = pygame.font.SysFont("Arial", 24, bold=True)

        text_surface = font.render(text_value, True, color)
        text_rect = text_surface.get_rect(center=(mid_x, mid_y - 10))

        self.screen.blit(text_surface, text_rect)