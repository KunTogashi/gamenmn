import cv2
import mediapipe as mp
import pygame
import sys
import random

# --- 1. Khởi tạo MediaPipe & OpenCV ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
cap = cv2.VideoCapture(0)

# --- 2. Khởi tạo Pygame ---
pygame.init() 
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Né Vật Cản")
clock = pygame.time.Clock()

# Màu sắc
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
LIGHT_VIOLET = (200, 162, 200)

# --- 3. Cài đặt các đối tượng game ---
# Kích thước
PLAYER_SIZE = 65
OBSTACLE_SIZE = 85
player_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2] 

# Tốc độ và Tần suất
OBSTACLE_SPEED_MIN_BASE = 5
OBSTACLE_SPEED_MAX_BASE = 8
BASE_OBSTACLE_SPAWN_RATE = 30
obstacles = []

# Tải hình ảnh
try:
    player_image_orig = pygame.image.load("player.png")
    obstacle_image_orig = pygame.image.load("obstacle.png")
    player_image = pygame.transform.scale(player_image_orig, (PLAYER_SIZE, PLAYER_SIZE)).convert_alpha()
    obstacle_image = pygame.transform.scale(obstacle_image_orig, (OBSTACLE_SIZE, OBSTACLE_SIZE)).convert_alpha()
    use_images = True
except pygame.error as e:
    print(f"LỖI TẢI ẢNH: {e}. Dùng hình mặc định.")
    use_images = False

# Tải Âm thanh
try:
    collision_sound = pygame.mixer.Sound("collision.wav")
    score_sound = pygame.mixer.Sound("score.wav")
    pygame.mixer.music.load("menu_music.mp3") 
    pygame.mixer.music.set_volume(0.4)
    use_sounds = True
except pygame.error as e:
    print(f"LỖI TẢI ÂM THANH: {e}. Chơi không có âm thanh.")
    use_sounds = False

# Tải Ảnh Nền Menu 
try:
    menu_bg_image_orig = pygame.image.load("menu_background.png")
    # Đảm bảo ảnh nền khớp kích thước màn hình
    menu_bg_image = pygame.transform.scale(menu_bg_image_orig, (SCREEN_WIDTH, SCREEN_HEIGHT))
    menu_bg_image = menu_bg_image.convert() # Tối ưu hóa ảnh 
    use_menu_bg = True
except pygame.error as e:
    print(f"LỖI: Không thể tải 'menu_background.png'. Sẽ dùng nền đen cho menu.")
    use_menu_bg = False


# Điểm số và trạng thái game
score = 0
high_score = 0
font = pygame.font.Font(None, 64)
small_font = pygame.font.Font(None, 40)
game_state = "START" 
start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50, 400, 100)
title_font = pygame.font.Font(None, 90) 

# --- 4. Các hàm hỗ trợ game ---
def create_obstacle(current_speed_max):
    side = random.choice(['top', 'bottom', 'left', 'right'])
    speed_x, speed_y = 0, 0
    speed_base = random.randint(OBSTACLE_SPEED_MIN_BASE, current_speed_max)
    if side == 'top':
        x, y = random.randint(0, SCREEN_WIDTH - OBSTACLE_SIZE), -OBSTACLE_SIZE
        speed_y = speed_base
    elif side == 'bottom':
        x, y = random.randint(0, SCREEN_WIDTH - OBSTACLE_SIZE), SCREEN_HEIGHT
        speed_y = -speed_base
    elif side == 'left':
        x, y = -OBSTACLE_SIZE, random.randint(0, SCREEN_HEIGHT - OBSTACLE_SIZE)
        speed_x = speed_base
    elif side == 'right':
        x, y = SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT - OBSTACLE_SIZE)
        speed_x = -speed_base
    obstacles.append({"rect": pygame.Rect(x, y, OBSTACLE_SIZE, OBSTACLE_SIZE), "speed_x": speed_x, "speed_y": speed_y})

def reset_game():
    global player_pos, obstacles, score, game_state
    player_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
    obstacles = []
    score = 0

print("Đang chạy game... Tải màn hình bắt đầu.")
if use_sounds:
    pygame.mixer.music.play(loops=-1)

# --- 5. Vòng lặp chính của Game ---
running = True
while running and cap.isOpened():

    # --- A. ĐỌC CAMERA ---
    success, frame = cap.read()
    if not success: break
    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # --- B. XỬ LÝ SỰ KIỆN & INPUT ---
    current_hand_pos = None
    if game_state == "PLAYING":
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            index_finger_x = hand_landmarks.landmark[8].x
            index_finger_y = hand_landmarks.landmark[8].y
            current_hand_pos = (int(index_finger_x * SCREEN_WIDTH), int(index_finger_y * SCREEN_HEIGHT))

    # Xử lý sự kiện (Chuột, Phím)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_state == "START":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    mouse_pos = event.pos 
                    if start_button_rect.collidepoint(mouse_pos):
                        reset_game() 
                        game_state = "PLAYING"
                        if use_sounds:
                            pygame.mixer.music.stop() # Dừng nhạc menu
                            pygame.mixer.music.load("background.mp3") # Tải nhạc game
                            pygame.mixer.music.play(loops=-1) # Phát nhạc game
        elif game_state == "GAME_OVER":
            if event.type == pygame.MOUSEBUTTONDOWN: # Nếu có sự kiện click chuột
                if event.button == 1: # 1 là click chuột trái
                    game_state = "START" # Quay về màn hình bắt đầu
                    if use_sounds:
                        pygame.mixer.music.load("menu_music.mp3") # Tải nhạc menu
                        pygame.mixer.music.play(loops=-1) # Phát nhạc menu
    # --- D. VẼ LÊN MÀN HÌNH ---

    if game_state == "START":
        # --- Nền Mở Đầu ---
        if use_menu_bg:
            screen.blit(menu_bg_image, (0, 0)) # Vẽ ảnh nền menu
        else:
            screen.fill(BLACK) # Dự phòng: nền đen

        # --- Vẽ Menu ---
        title_text = title_font.render("NAME GAME", True, LIGHT_VIOLET)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 4))
        high_score_text = small_font.render(f"HIGH SCORE: {high_score}", True, WHITE)
        screen.blit(high_score_text, (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, SCREEN_HEIGHT // 4 + 70))
        pygame.draw.rect(screen, GREEN, start_button_rect, border_radius=15)
        start_text = font.render("START", True, BLACK) 
        screen.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
        guide_text = small_font.render("Have fun", True, WHITE)
        screen.blit(guide_text, (SCREEN_WIDTH // 2 - guide_text.get_width() // 2, SCREEN_HEIGHT // 2 + 70))
    
    else: 
        # --- Nền Game (Camera) cho PLAYING và GAME_OVER ---
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_pygame = pygame.surfarray.make_surface(frame_rgb)
        frame_pygame = pygame.transform.rotate(frame_pygame, -90)
        frame_pygame = pygame.transform.flip(frame_pygame, True, False)
        screen.blit(frame_pygame, (0, 0)) # Vẽ nền camera

        if game_state == "PLAYING":
            # --- Logic khi đang chơi (Dùng TAY) ---
            if current_hand_pos:
                player_pos[0] = current_hand_pos[0]
                player_pos[1] = current_hand_pos[1]
            player_pos[0] = max(PLAYER_SIZE // 2, min(player_pos[0], SCREEN_WIDTH - PLAYER_SIZE // 2))
            player_pos[1] = max(PLAYER_SIZE // 2, min(player_pos[1], SCREEN_HEIGHT - PLAYER_SIZE // 2))

            # Cập nhật logic game
            current_spawn_rate = max(10, BASE_OBSTACLE_SPAWN_RATE - (score // 3)) 
            current_speed_max = OBSTACLE_SPEED_MAX_BASE + (score // 5)
            if random.randint(1, int(current_spawn_rate)) == 1:
                create_obstacle(current_speed_max)
            player_rect = pygame.Rect(player_pos[0] - PLAYER_SIZE // 2, player_pos[1] - PLAYER_SIZE // 2, PLAYER_SIZE, PLAYER_SIZE)
            for obstacle in list(obstacles):
                obstacle["rect"].x += obstacle["speed_x"]
                obstacle["rect"].y += obstacle["speed_y"]
                if player_rect.colliderect(obstacle["rect"]):
                    game_state = "GAME_OVER" 
                    if use_sounds:
                        collision_sound.play()
                        pygame.mixer.music.stop()
                    if score > high_score:
                        high_score = score
                if (obstacle["rect"].right < -100 or 
                    obstacle["rect"].left > SCREEN_WIDTH + 100 or
                    obstacle["rect"].bottom < -100 or 
                    obstacle["rect"].top > SCREEN_HEIGHT + 100):
                    obstacles.remove(obstacle)
                    score += 1
                    if use_sounds:
                        score_sound.play()
            
            # --- Vẽ khi đang chơi ---
            if use_images:
                player_draw_pos = (player_pos[0] - PLAYER_SIZE // 2, player_pos[1] - PLAYER_SIZE // 2)
                screen.blit(player_image, player_draw_pos)
            else:
                pygame.draw.circle(screen, (0, 0, 255), player_pos, PLAYER_SIZE // 2)
            for obstacle in obstacles:
                if use_images:
                    screen.blit(obstacle_image, obstacle["rect"].topleft)
                else:
                    pygame.draw.rect(screen, (255, 0, 0), obstacle["rect"])
            score_text = font.render(f"Score: {score}", True, GREEN)
            screen.blit(score_text, (10, 10))

        elif game_state == "GAME_OVER":
            # --- Vẽ màn hình Game Over ---
            game_over_text = font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            score_text = small_font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 + 10))
            restart_text = small_font.render("Click anywhere to return to Menu", True, WHITE) 
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 70))

    # --- CẬP NHẬT MÀN HÌNH ---
    pygame.display.flip()
    clock.tick(120)

# --- 6. Dọn dẹp ---
cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()