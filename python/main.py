import asyncio
import random
import sys
import os

# ★★★★★ 最終対策 1: オーディオドライバを完全に無効化 ★★★★★
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame

# --- デバッグ用メッセージ表示関数 ---
def draw_debug_message(screen, message, color=(0,0,0)):
    screen.fill(color)
    font = pygame.font.Font(None, 36)
    text_surface = font.render(message, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(300 // 2, 500 // 2))
    screen.blit(text_surface, text_rect)
    pygame.display.flip()

async def main():
    # --- デバッグ: Pygame初期化前 ---
    # このメッセージすら表示されない場合、import自体に問題がある
    # print("DEBUG: Before pygame.init()")

    pygame.init()

    # 画面設定
    SCREEN_WIDTH, SCREEN_HEIGHT = 300, 500
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("画像パズル")

    # --- デバッグ: 画面設定後 ---
    draw_debug_message(screen, "1. Screen Initialized", (255,0,0)) # 赤画面
    await asyncio.sleep(0.5)

    # 色などの基本設定
    WHITE, BLACK, GREEN, BLUE, RED, GRAY = (255,255,255), (0,0,0), (0,255,0), (0,0,255), (255,0,0), (128,128,128)
    background_size = (250, 350)
    background_pos = (SCREEN_WIDTH//2-background_size[0]//2, SCREEN_HEIGHT//2-background_size[1]//2-70)
    piece_positions = {
        "head.png": (background_pos[0]+123, background_pos[1]+26), "costa.png": (background_pos[0]+123, background_pos[1]+85),
        "backbone.png": (background_pos[0]+123, background_pos[1]+110), "pelvis.png": (background_pos[0]+123, background_pos[1]+155),
        "right_arm.png": (background_pos[0]+50, background_pos[1]+130), "left_arm.png": (background_pos[0]+200, background_pos[1]+130),
        "right_femur.png": (background_pos[0]+98, background_pos[1]+202), "left_femur.png": (background_pos[0]+152, background_pos[1]+202),
        "right_knee.png": (background_pos[0]+103, background_pos[1]+237), "left_knee.png": (background_pos[0]+147, background_pos[1]+237),
        "right_leg.png": (background_pos[0]+105, background_pos[1]+294), "left_leg.png": (background_pos[0]+145, background_pos[1]+294),
    }
    drawing_order = ["backbone.png", "costa.png", "pelvis.png", "right_femur.png", "left_femur.png", "right_leg.png", "left_leg.png", "right_arm.png", "left_arm.png", "head.png", "right_knee.png", "left_knee.png"]
    piece_names = drawing_order
    base_piece_height = 45
    piece_scale_multipliers = { "head.png":1.12, "backbone.png":2.8, "costa.png":1.25, "pelvis.png":1.15, "right_arm.png":3.3, "left_arm.png":3.3, "right_femur.png":1.76, "left_femur.png":1.76, "right_knee.png":0.42, "left_knee.png":0.42, "right_leg.png":2.28, "left_leg.png":2.28 }
    piece_rotations = { "right_arm.png": -9.4, "left_arm.png": 9.4 }
    
    def create_piece_frame(piece_image): return pygame.Surface(piece_image.get_size(), pygame.SRCALPHA)
    def create_default_image(size, color=GREEN):
        surface = pygame.Surface(size, pygame.SRCALPHA); s = max(1, min(size[0], size[1])//2-5)
        pygame.draw.circle(surface, color, (size[0]//2, size[1]//2), s); pygame.draw.circle(surface, BLACK, (size[0]//2, size[1]//2), s, 3)
        return surface

    # --- デバッグ: 画像読み込み開始前 ---
    draw_debug_message(screen, "2. Starting Image Load", (0,255,0)) # 緑画面
    await asyncio.sleep(0.5)

    piece_images_dict, frame_images_dict = {}, {}
    background_image, reset_button_image = None, None
    ASSETS_PATH = "assets"
    image_files = { "human": "human.png", "reset": "reset.png" }

    for i, piece_name in enumerate(piece_names):
        draw_debug_message(screen, f"Load: {piece_name} ({i+1}/{len(piece_names)})", (0,0,255)) # 青画面
        
        # ★★★★★ 最終対策 2: 処理を分割し、ブラウザに休憩時間を与える ★★★★★
        await asyncio.sleep(0) 

        multiplier = piece_scale_multipliers.get(piece_name, 1.0); target_h = base_piece_height * multiplier
        angle = piece_rotations.get(piece_name, 0); image_path = os.path.join(ASSETS_PATH, piece_name)
        try:
            original_image = pygame.image.load(image_path).convert_alpha()
            original_width, original_height = original_image.get_size()
            aspect_ratio = original_width/original_height if original_height > 0 else 1
            new_width, new_height = int(target_h*aspect_ratio), int(target_h)
            resized_image = pygame.transform.scale(original_image, (new_width, new_height))
            final_image = pygame.transform.rotate(resized_image, angle) if angle != 0 else resized_image
            piece_images_dict[piece_name] = final_image
        except pygame.error:
            piece_images_dict[piece_name] = create_default_image((int(target_h), int(target_h)))
        frame_images_dict[piece_name] = create_piece_frame(piece_images_dict[piece_name])
    try:
        background_image_path = os.path.join(ASSETS_PATH, image_files["human"])
        background_image = pygame.transform.scale(pygame.image.load(background_image_path).convert_alpha(), background_size)
    except pygame.error: pass
    try:
        reset_button_image_path = os.path.join(ASSETS_PATH, image_files["reset"])
        reset_button_image = pygame.transform.scale(pygame.image.load(reset_button_image_path).convert_alpha(), (55, 30))
    except pygame.error: pass

    # --- デバッグ: 全変数初期化完了 ---
    draw_debug_message(screen, "3. Setup Complete!", (255,255,0)) # 黄色画面
    await asyncio.sleep(0.5)

    # (ここから先のゲームロジックは変更なし)
    font = pygame.font.Font(None, 50); complete_text_render = font.render("Complete!", True, RED)
    reset_button_rect = pygame.Rect(SCREEN_WIDTH-65, 10, 55, 30); piece_start_positions = {}
    spacing_x = int(base_piece_height*1.4); start_x = spacing_x; start_y = 440
    for i, name in enumerate(piece_names): piece_start_positions[name] = [start_x + i*spacing_x, start_y]
    def shuffle_pieces():
        shuffled_list = list(piece_names); random.shuffle(shuffled_list); new_positions = {}
        for i, name in enumerate(shuffled_list): new_positions[name] = [start_x+i*spacing_x, start_y]
        return new_positions
    current_piece_positions = piece_start_positions.copy(); puzzle_done_state = {name: False for name in piece_names}
    scroll_x = 0; scroll_speed = 40; total_pieces_width = start_x*2+(len(piece_names)-1)*spacing_x
    max_scroll_x = total_pieces_width-SCREEN_WIDTH if total_pieces_width > SCREEN_WIDTH else 0
    left_arrow_rect, right_arrow_rect = pygame.Rect(5, start_y-20, 30, 40), pygame.Rect(SCREEN_WIDTH-35, start_y-20, 30, 40)
    dragging_piece = None; drag_offset_x, drag_offset_y = 0, 0; swiping_slider = False; swipe_start_x, initial_scroll_x = 0, 0
    running = True; clock = pygame.time.Clock(); FPS = 60

    # --- メインループ ---
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if all(puzzle_done_state.values()) and reset_button_rect.collidepoint(mouse_pos):
                    piece_start_positions=shuffle_pieces(); current_piece_positions=piece_start_positions.copy()
                    puzzle_done_state={name:False for name in piece_names}; scroll_x=0; continue
                if left_arrow_rect.collidepoint(mouse_pos): scroll_x=max(0, scroll_x-scroll_speed); continue
                if right_arrow_rect.collidepoint(mouse_pos): scroll_x=min(max_scroll_x, scroll_x+scroll_speed); continue
                slider_area=pygame.Rect(0, start_y-40, SCREEN_WIDTH, 100); piece_clicked_on_slider = False
                if slider_area.collidepoint(mouse_pos):
                    for name in reversed(drawing_order):
                        if not puzzle_done_state.get(name):
                            on_screen_x=piece_start_positions[name][0]-scroll_x; on_screen_y=piece_start_positions[name][1]
                            rect=piece_images_dict[name].get_rect(center=(on_screen_x, on_screen_y))
                            if rect.collidepoint(mouse_pos):
                                dragging_piece=name; current_piece_positions[name]=list(mouse_pos)
                                drag_offset_x=mouse_pos[0]-on_screen_x; drag_offset_y=mouse_pos[1]-on_screen_y
                                piece_clicked_on_slider=True; break
                if not piece_clicked_on_slider and slider_area.collidepoint(mouse_pos):
                    swiping_slider=True; swipe_start_x=mouse_pos[0]; initial_scroll_x=scroll_x
            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging_piece:
                    dist=pygame.math.Vector2(current_piece_positions[dragging_piece]).distance_to(piece_positions[dragging_piece])
                    if dist <= 25:
                        current_piece_positions[dragging_piece]=list(piece_positions[dragging_piece])
                        puzzle_done_state[dragging_piece]=True
                    dragging_piece=None
                swiping_slider = False
            elif event.type == pygame.MOUSEMOTION:
                if dragging_piece: current_piece_positions[dragging_piece]=list(event.pos)
                elif swiping_slider:
                    mouse_x=event.pos[0]; swipe_distance=swipe_start_x-mouse_x
                    scroll_x=max(0, min(max_scroll_x, initial_scroll_x+swipe_distance))
        screen.fill(WHITE)
        if background_image: screen.blit(background_image, background_pos)
        for piece_name, pos in piece_positions.items():
            if not puzzle_done_state.get(piece_name):
                frame_img=frame_images_dict[piece_name]; screen.blit(frame_img, frame_img.get_rect(center=pos))
        for name in drawing_order:
            img=piece_images_dict[name]
            if name == dragging_piece or puzzle_done_state.get(name):
                 pos=current_piece_positions[name]; screen.blit(img, img.get_rect(center=pos))
            else:
                on_screen_x=piece_start_positions[name][0]-scroll_x; on_screen_y=piece_start_positions[name][1]
                rect=img.get_rect(center=(int(on_screen_x), int(on_screen_y)))
                if rect.right > 0 and rect.left < SCREEN_WIDTH: screen.blit(img, rect)
        pygame.draw.polygon(screen, GRAY, [(left_arrow_rect.left+5, left_arrow_rect.centery), (left_arrow_rect.right-5, left_arrow_rect.top+5), (left_arrow_rect.right-5, left_arrow_rect.bottom-5)])
        pygame.draw.polygon(screen, GRAY, [(right_arrow_rect.right-5, right_arrow_rect.centery), (right_arrow_rect.left+5, right_arrow_rect.top+5), (right_arrow_rect.left+5, right_arrow_rect.bottom-5)])
        if all(puzzle_done_state.values()):
            if reset_button_image: screen.blit(reset_button_image, reset_button_rect)
            else: pygame.draw.rect(screen, BLUE, reset_button_rect)
            screen.blit(complete_text_render, complete_text_render.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT-60)))
        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(FPS)

if __name__ == "__main__":
    asyncio.run(main())