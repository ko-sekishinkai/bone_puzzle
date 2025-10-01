import asyncio
import random
import sys
import os
import webbrowser

# このスクリプトファイル自身の場所を基準にパスを解決するように変更
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame

# 画面にテキストを描画するための関数
def draw_text(screen, text, font, color, pos, is_center=True):
    text_surface = font.render(text, True, color)
    if is_center:
        text_rect = text_surface.get_rect(center=pos)
    else:
        text_rect = text_surface.get_rect(topleft=pos)
    screen.blit(text_surface, text_rect)

async def main():
    # pygame.init() はmixerを初期化する前に個別に呼び出す
    pygame.font.init()
    pygame.display.init()

    # 画面設定
    SCREEN_WIDTH, SCREEN_HEIGHT = 300, 500
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ほねほねパズル")
    
    # 色などの基本設定
    WHITE, BLACK, GREEN, BLUE, RED, GRAY = (255,255,255), (0,0,0), (0,255,0), (0,0,255), (255,0,0), (128,128,128)
    LINK_COLOR = (100, 100, 255)
    ASSETS_PATH = "assets"

    # --- フォントの準備 ---
    try:
        font_path = os.path.join(ASSETS_PATH, "NotoSansJP-Bold.ttf")
        jp_font_40 = pygame.font.Font(font_path, 40)
        jp_font_36 = pygame.font.Font(font_path, 36)
    except pygame.error:
        jp_font_40 = pygame.font.Font(None, 60)
        jp_font_36 = pygame.font.Font(None, 50)
    
    font_50 = pygame.font.Font(None, 50)
    font_24 = pygame.font.Font(None, 24)
    font_18 = pygame.font.Font(None, 18)

    # --- タイトル画面の表示 ---
    screen.fill(WHITE)
    draw_text(screen, "ほねほねパズル", jp_font_40, BLACK, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    pygame.display.flip()
    await asyncio.sleep(2.5)
    
    # 効果音関連
    is_mixer_initialized = False
    try:
        # ここで "drop.ogg" を読み込んでいます
        drop_sound = pygame.mixer.Sound(os.path.join(ASSETS_PATH, "drop.ogg"))
        clear_sound = pygame.mixer.Sound(os.path.join(ASSETS_PATH, "clear.ogg"))
    except pygame.error as e:
        print(f"効果音ファイルの読み込みに失敗しました: {e}")
        class DummySound:
            def play(self): pass
        drop_sound = clear_sound = DummySound()

    # --- ゲームの基本設定 ---
    background_size = (250, 350)
    background_pos = (SCREEN_WIDTH//2-background_size[0]//2, SCREEN_HEIGHT//2-background_size[1]//2-70)
    
    original_bone_pieces = ["backbone.png", "costa.png", "pelvis.png", "right_femur.png", "left_femur.png", "right_leg.png", "left_leg.png", "right_arm.png", "left_arm.png", "head.png", "right_knee.png", "left_knee.png"]
    
    piece_positions = { "head.png": (background_pos[0]+123, background_pos[1]+26), "costa.png": (background_pos[0]+123, background_pos[1]+85), "backbone.png": (background_pos[0]+123, background_pos[1]+110), "pelvis.png": (background_pos[0]+123, background_pos[1]+155), "right_arm.png": (background_pos[0]+50, background_pos[1]+130), "left_arm.png": (background_pos[0]+200, background_pos[1]+130), "right_femur.png": (background_pos[0]+98, background_pos[1]+202), "left_femur.png": (background_pos[0]+152, background_pos[1]+202), "right_knee.png": (background_pos[0]+103, background_pos[1]+237), "left_knee.png": (background_pos[0]+147, background_pos[1]+237), "right_leg.png": (background_pos[0]+105, background_pos[1]+294), "left_leg.png": (background_pos[0]+145, background_pos[1]+294), }
    base_piece_height = 45
    piece_scale_multipliers = { "head.png":1.12, "backbone.png":2.8, "costa.png":1.25, "pelvis.png":1.15, "right_arm.png":3.3, "left_arm.png":3.3, "right_femur.png":1.76, "left_femur.png":1.76, "right_knee.png":0.42, "left_knee.png":0.42, "right_leg.png":2.28, "left_leg.png":2.28 }
    piece_rotations = { "right_arm.png": -9.4, "left_arm.png": 9.4 }
    piece_drag_inflations = { "default": 20, "right_knee.png": 40, "left_knee.png": 40 }
    
    piece_images_dict, frame_images_dict = {}, {}
    image_files = { "human": "human.png", "reset": "reset.png", "github": "github_icon.png" }
    all_piece_names_to_load = original_bone_pieces + ["unchi.png"]

    for name in all_piece_names_to_load:
        await asyncio.sleep(0)
        image_path = os.path.join(ASSETS_PATH, name)
        try:
            original_image = pygame.image.load(image_path).convert_alpha()
            if name == "unchi.png": final_image = pygame.transform.scale(original_image, (50, 50))
            else:
                multiplier = piece_scale_multipliers.get(name, 1.0); target_h = base_piece_height * multiplier; angle = piece_rotations.get(name, 0); w, h = original_image.get_size(); aspect = w/h if h > 0 else 1; new_w, new_h = int(target_h * aspect), int(target_h); resized_image = pygame.transform.scale(original_image, (new_w, new_h)); final_image = pygame.transform.rotate(resized_image, angle)
            piece_images_dict[name] = final_image
        except pygame.error: piece_images_dict[name] = pygame.Surface((50,50), pygame.SRCALPHA)
        if name != "unchi.png": frame_images_dict[name] = pygame.Surface(piece_images_dict[name].get_size(), pygame.SRCALPHA)

    background_image = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS_PATH, image_files["human"])).convert_alpha(), background_size)
    reset_button_image = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS_PATH, image_files["reset"])).convert_alpha(), (55, 30))
    github_icon_image = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS_PATH, image_files["github"])).convert_alpha(), (30, 30))
    
    pelvis_center = piece_positions["pelvis.png"]
    unchi_target_pos = (pelvis_center[0], pelvis_center[1] + 70) 

    congrats_text_render = jp_font_36.render("おめでとう！", True, RED)

    reset_button_rect = pygame.Rect(SCREEN_WIDTH-65, 10, 55, 30); start_y = 440; spacing_x = int(base_piece_height * 2.4); left_arrow_rect, right_arrow_rect = pygame.Rect(5, start_y-20, 30, 40), pygame.Rect(SCREEN_WIDTH-35, start_y-20, 30, 40)
    
    license_text_str, license_url = "MIT License", "https://github.com/ko-sekishinkai/bone_puzzle/blob/main/LICENSE"; github_url = "https://github.com/ko-sekishinkai/bone_puzzle"; license_surface_normal = font_18.render(license_text_str, True, GRAY); license_surface_hover = font_18.render(license_text_str, True, LINK_COLOR); license_rect = license_surface_normal.get_rect(topleft=(5, 5)); github_icon_rect = github_icon_image.get_rect(topleft=(license_rect.left, license_rect.bottom + 5))

    game_level = 1; reset_count = 0; piece_names = []; drawing_order = []; piece_start_positions = {}; current_piece_positions = {}; puzzle_done_state = {}; scroll_x = 0; total_pieces_width = 1
    
    continuous_scroll_speed = 5
    scrolling_left = False
    scrolling_right = False

    def reset_game_to_level1():
        nonlocal piece_names, drawing_order, piece_start_positions, current_piece_positions, puzzle_done_state, scroll_x, total_pieces_width, game_level
        game_level = 1; piece_names = list(original_bone_pieces); drawing_order = list(original_bone_pieces); random.shuffle(piece_names) 
        start_x = spacing_x; temp_positions = {}; 
        for i, name in enumerate(piece_names): temp_positions[name] = [start_x + i*spacing_x, start_y]
        piece_start_positions = temp_positions.copy(); current_piece_positions = temp_positions.copy(); puzzle_done_state = {name: False for name in original_bone_pieces}
        scroll_x = 0; total_pieces_width = len(original_bone_pieces) * spacing_x
        if total_pieces_width == 0: total_pieces_width = 1

    reset_game_to_level1()

    dragging_piece = None; swiping_slider = False; swipe_start_x, initial_scroll_x = 0, 0

    running = True; clock = pygame.time.Clock(); FPS = 60
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        is_hovering_license = license_rect.collidepoint(mouse_pos)
        is_hovering_github = github_icon_rect.collidepoint(mouse_pos)
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if is_hovering_license or is_hovering_github else pygame.SYSTEM_CURSOR_ARROW)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not is_mixer_initialized:
                    try:
                        pygame.mixer.init(); is_mixer_initialized = True; print("Audio Mixer Initialized!")
                    except pygame.error as e: print(f"Mixerの初期化に失敗: {e}")

                if is_hovering_license: webbrowser.open(license_url); continue
                if is_hovering_github: webbrowser.open(github_url); continue
                
                if game_level == 2 and puzzle_done_state.get("unchi.png") and reset_button_rect.collidepoint(mouse_pos):
                    reset_count += 1; reset_game_to_level1(); continue

                if left_arrow_rect.collidepoint(mouse_pos): scrolling_left = True
                elif right_arrow_rect.collidepoint(mouse_pos): scrolling_right = True
                else:
                    slider_area = pygame.Rect(0, start_y - 40, SCREEN_WIDTH, 100); piece_clicked = False
                    if slider_area.collidepoint(mouse_pos):
                        for name in reversed(piece_names):
                            if not puzzle_done_state.get(name):
                                offsets = [0, total_pieces_width, -total_pieces_width] if game_level == 1 else [0]
                                for offset in offsets:
                                    on_screen_x = piece_start_positions[name][0] - scroll_x + offset
                                    rect = piece_images_dict[name].get_rect(center=(on_screen_x, start_y)); inflation = piece_drag_inflations.get(name, piece_drag_inflations["default"])
                                    if rect.inflate(inflation, inflation).collidepoint(mouse_pos):
                                        dragging_piece = name; current_piece_positions[name] = list(mouse_pos); piece_clicked = True; break
                            if piece_clicked: break
                    if not piece_clicked and slider_area.collidepoint(mouse_pos):
                        swiping_slider = True; swipe_start_x = mouse_pos[0]; initial_scroll_x = scroll_x

            elif event.type == pygame.MOUSEBUTTONUP:
                scrolling_left = False
                scrolling_right = False
                
                if dragging_piece:
                    target_pos = unchi_target_pos if dragging_piece == "unchi.png" else piece_positions[dragging_piece]
                    dist = pygame.math.Vector2(current_piece_positions[dragging_piece]).distance_to(target_pos)
                    if dist <= 35:
                        current_piece_positions[dragging_piece] = list(target_pos)
                        puzzle_done_state[dragging_piece] = True
                        
                        # --- ▼▼▼ ここが効果音を再生している部分です ▼▼▼ ---
                        if is_mixer_initialized:
                            # もし置いたのが "unchi.png" ならクリア音
                            if dragging_piece == "unchi.png": 
                                clear_sound.play()
                            # それ以外のピース（骨）ならドロップ音
                            else: 
                                drop_sound.play()
                        # --- ▲▲▲ ここまで ▲▲▲ ---

                    dragging_piece = None
                swiping_slider = False

            elif event.type == pygame.MOUSEMOTION:
                if dragging_piece: current_piece_positions[dragging_piece] = list(event.pos)
                elif swiping_slider:
                    swipe_distance = swipe_start_x - event.pos[0]
                    if game_level == 1: scroll_x = (initial_scroll_x + swipe_distance) % total_pieces_width
                    else: scroll_x = max(0, min(0, initial_scroll_x + swipe_distance))

        if scrolling_left:
            scroll_x = (scroll_x - continuous_scroll_speed) % total_pieces_width
        if scrolling_right:
            scroll_x = (scroll_x + continuous_scroll_speed) % total_pieces_width

        is_level1_complete = all(puzzle_done_state.get(name, False) for name in original_bone_pieces)
        if game_level == 1 and is_level1_complete:
            game_level = 2; piece_names = ["unchi.png"]; drawing_order = ["unchi.png"]; start_pos_x = SCREEN_WIDTH // 2
            piece_start_positions = {"unchi.png": [start_x, start_y]}; current_piece_positions["unchi.png"] = [start_x, start_y]
            puzzle_done_state["unchi.png"] = False; scroll_x = 0; total_pieces_width = 1

        screen.fill(WHITE); screen.blit(background_image, background_pos)

        if game_level == 1:
            for name, pos in piece_positions.items():
                if not puzzle_done_state.get(name):
                    frame_img = frame_images_dict[name]; screen.blit(frame_img, frame_img.get_rect(center=pos))
        
        all_pieces_to_draw = list(original_bone_pieces) + ["unchi.png"]
        for name in all_pieces_to_draw:
             if puzzle_done_state.get(name) or name == dragging_piece:
                img = piece_images_dict.get(name)
                if img:
                    pos = current_piece_positions.get(name)
                    if pos: screen.blit(img, img.get_rect(center=pos))

        for name in piece_names:
            if not puzzle_done_state.get(name) and name != dragging_piece:
                img = piece_images_dict[name]; offsets = [0, total_pieces_width, -total_pieces_width] if game_level == 1 else [0]
                for offset in offsets:
                    on_screen_x = piece_start_positions[name][0] - scroll_x + offset
                    rect = img.get_rect(center=(int(on_screen_x), start_y))
                    if rect.right > 0 and rect.left < SCREEN_WIDTH: screen.blit(img, rect)

        if game_level == 1:
            pygame.draw.polygon(screen, GRAY, [(left_arrow_rect.left+5, left_arrow_rect.centery), (left_arrow_rect.right-5, left_arrow_rect.top+5), (left_arrow_rect.right-5, left_arrow_rect.bottom-5)])
            pygame.draw.polygon(screen, GRAY, [(right_arrow_rect.right-5, right_arrow_rect.centery), (right_arrow_rect.left+5, right_arrow_rect.top+5), (right_arrow_rect.left+5, right_arrow_rect.bottom-5)])
        
        if game_level == 2 and puzzle_done_state.get("unchi.png"):
            screen.blit(congrats_text_render, congrats_text_render.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT-60)))
            screen.blit(reset_button_image, reset_button_rect)
        
        draw_text(screen, f"Resets: {reset_count}", font_24, BLACK, (reset_button_rect.centerx, reset_button_rect.bottom + 15))

        screen.blit(license_surface_hover if is_hovering_license else license_surface_normal, license_rect)
        screen.blit(github_icon_image, github_icon_rect)
        
        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(FPS)

if __name__ == "__main__":
    asyncio.run(main())