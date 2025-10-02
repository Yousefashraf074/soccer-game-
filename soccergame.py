import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import sys

# Game constants
WIDTH, HEIGHT = 1200, 800
MAX_ARROW_LENGTH = 150

# Colors (RGB scaled 0-1 for OpenGL)
GREEN = (0, 0.5, 0)
WHITE = (1, 1, 1)
BLUE = (0.12, 0.56, 1)
RED = (0.86, 0.08, 0.24)
YELLOW = (1, 1, 0)
BLACK = (0, 0, 0)
DARK_GRAY = (0.2, 0.2, 0.2)

# Game state
ball_pos = [600, 400]
ball_velocity = [0, 0]
ball_team = "A"
ball_mass = 0.5

selected_player_index = 0
current_turn = "A"

score_a = 0
score_b = 0

shooting = False
shoot_start = None

PITCH_X_MIN, PITCH_X_MAX = 50, 1150
PITCH_Y_MIN, PITCH_Y_MAX = 50, 750

def init_opengl():
    glViewport(0, 0, WIDTH, HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glClearColor(*GREEN, 1)

def draw_text(x, y, text, font_size=36, color=(255, 255, 255)):
    # Scale color from 0-255 to 0-1 for OpenGL
    opengl_color = (color[0] / 255, color[1] / 255, color[2] / 255)
    
    font = pygame.font.SysFont("Arial", font_size, bold=True)
    text_surface = font.render(text, True, color)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)

    glWindowPos2f(x, HEIGHT - y)
    glColor3f(*opengl_color)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

def draw_filled_rect(x, y, width, height, color=(0, 0, 0), alpha=0.5):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(color[0] / 255, color[1] / 255, color[2] / 255, alpha)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()
    glDisable(GL_BLEND)
    glColor4f(1, 1, 1, 1)  # Reset color

def draw_score():
    # Create a surface with the score text
    font = pygame.font.SysFont("Arial", 48, bold=True)
    score_text = f"{score_a}:{score_b}"
    text_surface = font.render(score_text, True, (255, 255, 255))
    
    # Get the size of the text
    text_width = text_surface.get_width()
    text_height = text_surface.get_height()
    
    # Create a surface for the background
    background = pygame.Surface((text_width + 40, text_height + 20), pygame.SRCALPHA)
    background.fill((0, 0, 0, 200))  # Semi-transparent black
    
    # Blit the text onto the background
    background.blit(text_surface, (20, 10))
    
    # Convert to OpenGL format
    text_data = pygame.image.tostring(background, "RGBA", True)
    
    # Draw the combined background and text
    glWindowPos2i(WIDTH//2 - (text_width + 40)//2, HEIGHT - 80)
    glDrawPixels(background.get_width(), background.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)

def draw_rect(x, y, w, h, color, width=1):
    glColor3f(*color)
    glLineWidth(width)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()

def draw_line(x1, y1, x2, y2, color, width=2):
    glColor3f(*color)
    glLineWidth(width)
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()

def draw_circle(x, y, radius, color, filled=True, segments=32, width=1):
    glColor3f(*color)
    glLineWidth(width)
    if filled:
        glBegin(GL_TRIANGLE_FAN)
    else:
        glBegin(GL_LINE_LOOP)
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        glVertex2f(x + radius * math.cos(angle), y + radius * math.sin(angle))
    glEnd()

def draw_arrow(start, end):
    draw_line(start[0], start[1], end[0], end[1], WHITE, 4)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 15
    left = (end[0] - length * math.cos(angle - 0.3), end[1] - length * math.sin(angle - 0.3))
    right = (end[0] - length * math.cos(angle + 0.3), end[1] - length * math.sin(angle + 0.3))
    glBegin(GL_TRIANGLES)
    glColor3f(*WHITE)
    glVertex2f(*end)
    glVertex2f(*left)
    glVertex2f(*right)
    glEnd()

def draw_pitch():
    for i in range(6):
        shade = 0.48 if i % 2 == 0 else 0.38
        glColor3f(0, shade, 0)
        glBegin(GL_QUADS)
        glVertex2f(50 + i * 183.33, 50)
        glVertex2f(50 + i * 183.33, 750)
        glVertex2f(50 + (i + 1) * 183.33, 750)
        glVertex2f(50 + (i + 1) * 183.33, 50)
        glEnd()

    draw_rect(50, 50, 1100, 700, WHITE, 5)
    draw_line(WIDTH // 2, 50, WIDTH // 2, HEIGHT - 50, WHITE, 3)
    draw_circle(WIDTH // 2, HEIGHT // 2, 70, WHITE, False, width=3)
    draw_circle(WIDTH // 2, HEIGHT // 2, 3, WHITE)

    draw_rect(50, HEIGHT // 2 - 110, 150, 220, WHITE, 3)
    draw_rect(50, HEIGHT // 2 - 55, 50, 110, WHITE, 3)
    draw_circle(150, HEIGHT // 2, 2, WHITE)

    draw_rect(WIDTH - 200, HEIGHT // 2 - 110, 150, 220, WHITE, 3)
    draw_rect(WIDTH - 100, HEIGHT // 2 - 55, 50, 110, WHITE, 3)
    draw_circle(WIDTH - 150, HEIGHT // 2, 2, WHITE)

    for corner in [(50, 50), (1150, 50), (50, 750), (1150, 750)]:
        cx, cy = corner
        glColor3f(*WHITE)
        glBegin(GL_LINE_STRIP)
        for i in range(9):
            angle = math.pi / 2 * i / 8
            if cx > WIDTH // 2:
                angle = math.pi - angle
            if cy > HEIGHT // 2:
                angle = -angle if cx < WIDTH // 2 else -math.pi + angle
            glVertex2f(cx + 10 * math.cos(angle), cy + 10 * math.sin(angle))
        glEnd()

def draw_ball(pos):
    x, y = pos
    draw_circle(x + 4, y + 4, 12, DARK_GRAY)
    draw_circle(x, y, 10, WHITE)
    for angle in range(0, 360, 72):
        rad = math.radians(angle)
        dx = 5 * math.cos(rad)
        dy = 5 * math.sin(rad)
        draw_circle(x + dx, y + dy, 2, BLACK)

def create_players():
    team_a = [
        [[300, 300], [0, 0], 1.0],
        [[300, 400], [0, 0], 1.0],
        [[300, 500], [0, 0], 1.0],
        [[100, 400], [0, 0], 1.5]
    ]
    team_b = [
        [[900, 300], [0, 0], 1.0],
        [[900, 400], [0, 0], 1.0],
        [[900, 500], [0, 0], 1.0],
        [[1100, 400], [0, 0], 1.5]
    ]
    return team_a, team_b

def draw_players(players_a, players_b, selected_index):
    for i, (pos, _, _) in enumerate(players_a):
        x, y = pos
        color = WHITE if i == 3 else BLUE
        if current_turn == "A" and i == selected_index:
            draw_circle(x, y, 22, WHITE, False, width=3)
        draw_circle(x + 5, y + 5, 17, DARK_GRAY)
        draw_circle(x, y, 15, color)

    for i, (pos, _, _) in enumerate(players_b):
        x, y = pos
        color = YELLOW if i == 3 else RED
        if current_turn == "B" and i == selected_index:
            draw_circle(x, y, 22, WHITE, False, width=3)
        draw_circle(x + 5, y + 5, 17, DARK_GRAY)
        draw_circle(x, y, 15, color)

def clamp_position(pos):
    pos[0] = max(PITCH_X_MIN, min(PITCH_X_MAX, pos[0]))
    pos[1] = max(PITCH_Y_MIN, min(PITCH_Y_MAX, pos[1]))

def move_object(obj, mass=1.0):
    pos, vel = obj[:2]
    pos[0] += vel[0]
    pos[1] += vel[1]
    clamp_position(pos)
    friction = 0.9 + (mass * 0.02)
    vel[0] *= friction
    vel[1] *= friction
    if math.hypot(*vel) < 0.2:
        vel[0], vel[1] = 0, 0

def move_ball():
    move_object([ball_pos, ball_velocity], ball_mass)

def move_players(players):
    for player in players:
        pos, vel, mass = player
        move_object([pos, vel], mass)

def check_players_collision(players):
    # Check collisions between all pairs of players
    for i in range(len(players)):
        pos1, vel1, mass1 = players[i]
        for j in range(i + 1, len(players)):
            pos2, vel2, mass2 = players[j]
            
            # Calculate distance between players
            dx = pos2[0] - pos1[0]
            dy = pos2[1] - pos1[1]
            distance = math.hypot(dx, dy)
            
            # If players are colliding
            if distance < 40:  # 20px radius for each player
                if distance == 0:  # Avoid division by zero
                    angle = 0
                else:
                    angle = math.atan2(dy, dx)
                
                # Calculate relative velocity
                rel_vel_x = vel2[0] - vel1[0]
                rel_vel_y = vel2[1] - vel1[1]
                
                # Calculate impulse
                total_mass = mass1 + mass2
                impulse = 2 * (rel_vel_x * math.cos(angle) + rel_vel_y * math.sin(angle)) / total_mass
                
                # Apply impulse to velocities
                vel1[0] += impulse * mass2 * math.cos(angle)
                vel1[1] += impulse * mass2 * math.sin(angle)
                vel2[0] -= impulse * mass1 * math.cos(angle)
                vel2[1] -= impulse * mass1 * math.sin(angle)
                
                # Push players apart to prevent sticking
                overlap = 40 - distance
                push_x = overlap * math.cos(angle) * 0.5
                push_y = overlap * math.sin(angle) * 0.5
                
                pos1[0] -= push_x
                pos1[1] -= push_y
                pos2[0] += push_x
                pos2[1] += push_y

def check_collision(player_pos, player_vel, player_mass):
    distance = math.hypot(player_pos[0] - ball_pos[0], player_pos[1] - ball_pos[1])
    if distance < 25:
        dx = ball_pos[0] - player_pos[0]
        dy = ball_pos[1] - player_pos[1]
        angle = math.atan2(dy, dx)
        rel_vel_x = ball_velocity[0] - player_vel[0]
        rel_vel_y = ball_velocity[1] - player_vel[1]
        total_mass = player_mass + ball_mass
        impulse = 2 * (rel_vel_x * math.cos(angle) + rel_vel_y * math.sin(angle)) / total_mass
        ball_velocity[0] -= impulse * player_mass * math.cos(angle)
        ball_velocity[1] -= impulse * player_mass * math.sin(angle)
        push_distance = 25 - distance
        ball_pos[0] += push_distance * math.cos(angle) * 0.1
        ball_pos[1] += push_distance * math.sin(angle) * 0.1

def check_goal():
    global score_a, score_b
    x, y = ball_pos
    if 40 <= x <= 50 and HEIGHT // 2 - 30 <= y <= HEIGHT // 2 + 30:
        score_b += 1
        reset_ball()
    elif WIDTH - 50 <= x <= WIDTH - 40 and HEIGHT // 2 - 30 <= y <= HEIGHT // 2 + 30:
        score_a += 1
        reset_ball()

def check_out_of_bounds():
    x, y = ball_pos
    return x < PITCH_X_MIN or x > PITCH_X_MAX or y < PITCH_Y_MIN or y > PITCH_Y_MAX

def reset_ball():
    global ball_pos, ball_velocity, ball_team
    ball_pos[:] = [600, 400]
    ball_velocity = [0, 0]
    ball_team = "A"

def main():
    global selected_player_index, shooting, shoot_start, ball_velocity, current_turn, ball_team

    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Football Game - OpenGL Version")
    pygame.font.init()
    clock = pygame.time.Clock()
    init_opengl()

    players_a, players_b = create_players()
    running = True

    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    shooting = True
                    shoot_start = pygame.mouse.get_pos()

            elif event.type == MOUSEBUTTONUP and shooting:
                shooting = False
                shoot_end = pygame.mouse.get_pos()
                team = players_a if current_turn == "A" else players_b
                player = team[selected_player_index]
                pos, vel, mass = player

                dx = shoot_end[0] - pos[0]
                dy = shoot_end[1] - pos[1]
                dist = math.hypot(dx, dy)

                if dist > MAX_ARROW_LENGTH:
                    scale = MAX_ARROW_LENGTH / dist
                    dx *= scale
                    dy *= scale

                if dist > 0:
                    force_factor = 10 / mass
                    player[1][0] = dx / force_factor
                    player[1][1] = dy / force_factor

                    if math.hypot(pos[0] + dx - ball_pos[0], pos[1] + dy - ball_pos[1]) <= 25:
                        ball_velocity = [dx / (10 * ball_mass), dy / (10 * ball_mass)]
                        ball_team = current_turn

                    current_turn = "B" if current_turn == "A" else "A"

            elif event.type == KEYDOWN and event.key == K_TAB:
                selected_player_index = (selected_player_index + 1) % 4

        # Move all objects
        move_ball()
        move_players(players_a)
        move_players(players_b)
        
        # Check for player-to-player collisions
        check_players_collision(players_a)
        check_players_collision(players_b)

        # Check player-ball collisions
        for team in [players_a, players_b]:
            for player in team:
                check_collision(player[0], player[1], player[2])

        check_goal()

        if check_out_of_bounds():
            reset_ball()
            current_turn = "B" if ball_team == "A" else "A"

        # Draw everything
        glClear(GL_COLOR_BUFFER_BIT)
        draw_pitch()
        draw_players(players_a, players_b, selected_player_index)
        draw_ball(ball_pos)
        
        # Ensure we're in 2D mode for score drawing
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, WIDTH, HEIGHT, 0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        draw_score()

        if shooting:
            team = players_a if current_turn == "A" else players_b
            pos = team[selected_player_index][0]
            mouse_pos = pygame.mouse.get_pos()
            dx = mouse_pos[0] - pos[0]
            dy = mouse_pos[1] - pos[1]
            dist = math.hypot(dx, dy)
            if dist > MAX_ARROW_LENGTH:
                scale = MAX_ARROW_LENGTH / dist
                mouse_pos = (pos[0] + dx * scale, pos[1] + dy * scale)
            draw_arrow(pos, mouse_pos)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
