import asyncio
import pygame
import random
import sys
import os

# ★★★ Pygbag対応：非同期対応のメイン関数を定義 ★★★
async def main():
    pygame.init()

    # 画面設定
    SCREEN_WIDTH, SCREEN_HEIGHT = 300, 500
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("画像パズル")

    # 色
    WHITE = (255, 255, 255); BLACK = (0, 0, 0); GREEN = (0, 255, 0); BLUE = (0, 0, 255); RED = (255, 0, 0); GRAY = (128, 128, 128)

    # パズル設定
    background_size = (250, 350)
    background_pos = (SCREEN_WIDTH // 2 - background_size[0] // 2, SCREEN_HEIGHT // 2 - background_size[1] // 2 - 70)

    # 各部位の枠の位置
    piece_positions = {
        "head.png": (background_pos[0] + 123, background_pos[1] + 26),
        "costa.png": (background_pos[0] + 123, background_pos[1] + 85),
        "backbone.png": (background_pos[0] + 123, background_pos[1] + 110),
        "pelvis.png": (background_pos[0] + 123, background_pos[1] + 155),
        "right_arm.png": (background_pos[0] + 50, background_pos[1] + 130),
        "left_arm.png": (background_pos[0] + 200, background_pos[1] + 130),
        "right_femur.png": (background_pos[0] + 98, background_pos[1] + 202),
        "left_femur.png": (background_pos[0] + 152, background_pos[1] + 202),
        "right_knee.png": (background_pos[0] + 103, background_pos[1] + 237),
        "left_knee.png": (background_pos[0] + 147, background_pos[1] + 237),
        "right_leg.png": (background_pos[0] + 105, background_pos[1] + 294),
        "left_leg.png": (background_pos[0] + 145, background_pos[1] + 294),
    }

    piece_size = 40  # 枠のサイズ

    # 描画順序を定義（下から上への順番）
    drawing_order = [
        "backbone.png",      # 一番下
        "costa.png",
        "pelvis.png",
        "right_femur.png",
        "left_femur.png",
        "right_leg.png",
        "left_leg.png",
        "right_arm.png",
        "left_arm.png",
        "head.png",
        "right_knee.png",    # 一番上
        "left_knee.png",     # 一番上
    ]

    piece_names = drawing_order

    # 全ピースの「基準となる高さ」を一つだけ設定
    base_piece_height = 45

    # 各ピースの「個別の倍率」を辞書で設定
    piece_scale_multipliers = {
        "head.png":1.12, "backbone.png":2.8,
        "costa.png":1.25, "pelvis.png":1.15,
        "right_arm.png":3.3, "left_arm.png":3.3, 
        "right_femur.png":1.76, "left_femur.png":1.76,
        "right_knee.png": 0.42, "left_knee.png": 0.42, 
        "right_leg.png":2.28, "left_leg.png":2.28,
    }

    # 各ピースの「回転角度」を辞書で設定
    piece_rotations = {
        "right_arm.png": -9.4,   # 右腕を少し時計回りに
        "left_arm.png": 9.4,    # 左腕を少し反時計回りに
    }

    # ★★★ 新規追加：ピース画像から枠画像を生成する関数 ★★★
    def create_piece_frame(piece_image, alpha=0, outline_width=0):
        """
        ピース画像から完全に透明な枠を生成（何も表示しない）
        alpha: 透明度（0=完全透明）
        outline_width: 輪郭線の太さ（0=輪郭線なし）
        """
        # 元画像のサイズを取得
        width, height = piece_image.get_size()
        
        # 新しいサーフェスを作成（アルファチャンネル付き）
        frame_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # 完全に透明なので何も描画しない
        
        return frame_surface

    # ★★★ 新規追加：ピースをランダム位置に配置する関数 ★★★
    def shuffle_pieces():
        shuffled_positions = piece_start_positions.copy()
        piece_list = list(piece_names)
        random.shuffle(piece_list)
        
        for i, name in enumerate(piece_list):
            shuffled_positions[name] = [start_x + i * spacing_x, start_y]
        
        return shuffled_positions

    piece_start_positions = {}
    spacing_x = int(base_piece_height * 1.4)
    start_x = spacing_x
    start_y = 440
    for i, name in enumerate(piece_names):
        piece_start_positions[name] = [start_x + i * spacing_x, start_y]

    scroll_x = 0; scroll_speed = 40
    total_pieces_width = start_x * 2 + (len(piece_names) - 1) * spacing_x
    max_scroll_x = total_pieces_width - SCREEN_WIDTH if total_pieces_width > SCREEN_WIDTH else 0
    left_arrow_rect = pygame.Rect(5, start_y - 20, 30, 40)
    right_arrow_rect = pygame.Rect(SCREEN_WIDTH - 35, start_y - 20, 30, 40)

    current_piece_positions = piece_start_positions.copy()
    puzzle_done_state = {name: False for name in piece_names}
    reset_button_rect = pygame.Rect(SCREEN_WIDTH - 65, 10, 55, 30)

    def create_default_image(size, color=GREEN):
        surface = pygame.Surface(size, pygame.SRCALPHA)
        s = max(1, min(size[0], size[1]) // 2 - 5)
        pygame.draw.circle(surface, color, (size[0]//2, size[1]//2), s)
        pygame.draw.circle(surface, BLACK, (size[0]//2, size[1]//2), s, 3)
        return surface

    # --- 画像読み込み処理 ---
    piece_images_dict = {}
    frame_image = None; background_image = None; reset_button_image = None
    # ★★★ 修正：ピース自体から作成した枠の辞書 ★★★
    frame_images_dict = {}

    print("\n画像を読み込み中...")

    for piece_name in piece_names:
        multiplier = piece_scale_multipliers.get(piece_name, 1.0)
        target_h = base_piece_height * multiplier
        angle = piece_rotations.get(piece_name, 0)

        # ★★★ Pygbag対応：try-except処理を簡素化 ★★★
        try:
            if os.path.exists(piece_name):
                original_image = pygame.image.load(piece_name)
                original_width, original_height = original_image.get_size()
                aspect_ratio = original_width / original_height if original_height > 0 else 1
                new_width = int(target_h * aspect_ratio)
                new_height = int(target_h)
                
                # まずリサイズ
                resized_image = pygame.transform.scale(original_image, (new_width, new_height))
                
                # 角度があれば回転させる
                if angle != 0:
                    final_image = pygame.transform.rotate(resized_image, angle)
                else:
                    final_image = resized_image
                    
                piece_images_dict[piece_name] = final_image
            else:
                piece_images_dict[piece_name] = create_default_image((int(target_h), int(target_h)))
        except:
            piece_images_dict[piece_name] = create_default_image((int(target_h), int(target_h)))

        # ★★★ 修正：ピース自体から枠画像を生成 ★★★
        frame_images_dict[piece_name] = create_piece_frame(piece_images_dict[piece_name])

    # 背景、リセットボタン画像の読み込み
    try:
        if os.path.exists("human.png"): 
            background_image = pygame.transform.scale(pygame.image.load("human.png"), background_size)
    except:
        background_image = None
        
    try:
        if os.path.exists("reset.png"): 
            reset_button_image = pygame.transform.scale(pygame.image.load("reset.png"), (reset_button_rect.width, reset_button_rect.height))
    except:
        reset_button_image = None

    font, font_small = pygame.font.Font(None, 50), pygame.font.Font(None, 24)
    reset_text, complete_text = "Reset", "Complete!"

    # ★★★ 新規追加：スワイプ操作用の変数 ★★★
    dragging_piece = None; drag_offset_x, drag_offset_y = 0, 0
    swiping_slider = False; swipe_start_x = 0; initial_scroll_x = 0
    running = True; clock = pygame.time.Clock(); FPS = 60

    # ★★★ Pygbag対応：メインループを非同期対応 ★★★
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if all(puzzle_done_state.values()) and reset_button_rect.collidepoint(mouse_pos):
                    piece_start_positions.update(shuffle_pieces())
                    current_piece_positions = piece_start_positions.copy()
                    puzzle_done_state = {name: False for name in piece_names}
                    scroll_x = 0
                    continue
                
                # ★★★ 修正：矢印ボタンとスワイプ操作を両方対応 ★★★
                if left_arrow_rect.collidepoint(mouse_pos):
                    scroll_x = max(0, scroll_x - scroll_speed); continue
                if right_arrow_rect.collidepoint(mouse_pos):
                    scroll_x = min(max_scroll_x, scroll_x + scroll_speed); continue
                
                # ★★★ 新規追加：スライダー領域でのスワイプ開始判定 ★★★
                slider_area = pygame.Rect(0, start_y - 40, SCREEN_WIDTH, 80)
                if slider_area.collidepoint(mouse_pos):
                    # まずピースのクリック判定を確認
                    piece_clicked = False
                    for name in reversed(drawing_order):
                        if not puzzle_done_state.get(name):
                            on_screen_x = current_piece_positions[name][0] - scroll_x
                            on_screen_y = current_piece_positions[name][1]
                            rect = piece_images_dict[name].get_rect(center=(on_screen_x, on_screen_y))
                            if rect.collidepoint(mouse_pos):
                                dragging_piece = name
                                drag_offset_x = mouse_pos[0] - on_screen_x
                                drag_offset_y = mouse_pos[1] - on_screen_y
                                piece_clicked = True
                                break
                    
                    # ピースがクリックされていない場合はスワイプ開始
                    if not piece_clicked:
                        swiping_slider = True
                        swipe_start_x = mouse_pos[0]
                        initial_scroll_x = scroll_x
                else:
                    # スライダー領域外でのピースクリック判定
                    for name in reversed(drawing_order):
                        if not puzzle_done_state.get(name):
                            on_screen_x = current_piece_positions[name][0] - scroll_x
                            on_screen_y = current_piece_positions[name][1]
                            rect = piece_images_dict[name].get_rect(center=(on_screen_x, on_screen_y))
                            if rect.collidepoint(mouse_pos):
                                dragging_piece = name
                                drag_offset_x = mouse_pos[0] - on_screen_x
                                drag_offset_y = mouse_pos[1] - on_screen_y
                                break
                            
            elif event.type == pygame.MOUSEBUTTONUP:
                # ★★★ 修正：スワイプ終了処理を追加 ★★★
                if swiping_slider:
                    swiping_slider = False
                elif dragging_piece:
                    if pygame.math.Vector2(current_piece_positions[dragging_piece]).distance_to(piece_positions[dragging_piece]) <= 25:
                        current_piece_positions[dragging_piece] = list(piece_positions[dragging_piece])
                        puzzle_done_state[dragging_piece] = True
                    else:
                        current_piece_positions[dragging_piece] = piece_start_positions[dragging_piece].copy()
                    dragging_piece = None
                    
            elif event.type == pygame.MOUSEMOTION:
                # ★★★ 修正：スワイプとピースドラッグを分離 ★★★
                if swiping_slider:
                    # スライダーのスワイプ操作
                    mouse_x = event.pos[0]
                    swipe_distance = swipe_start_x - mouse_x  # 右スワイプで負、左スワイプで正
                    new_scroll_x = initial_scroll_x + swipe_distance
                    scroll_x = max(0, min(max_scroll_x, new_scroll_x))
                elif dragging_piece:
                    # ピースのドラッグ操作
                    current_piece_positions[dragging_piece] = [event.pos[0] - drag_offset_x, event.pos[1] - drag_offset_y]
        
        screen.fill(WHITE)
        if background_image: 
            screen.blit(background_image, background_pos)
        
        # ★★★ 修正：ピース自体から作成した枠を描画 ★★★
        for piece_name, pos in piece_positions.items():
            if not puzzle_done_state.get(piece_name):  # まだ配置されていないピースの枠のみ表示
                frame_img = frame_images_dict[piece_name]
                screen.blit(frame_img, frame_img.get_rect(center=pos))
        
        # 描画順序に従って描画
        for name in drawing_order:
            img = piece_images_dict[name]
            if puzzle_done_state.get(name) or name == dragging_piece:
                screen.blit(img, img.get_rect(center=current_piece_positions[name]))
            else:
                on_screen_x = current_piece_positions[name][0] - scroll_x
                on_screen_y = current_piece_positions[name][1]
                rect = img.get_rect(center=(int(on_screen_x), int(on_screen_y)))
                if rect.right > 0 and rect.left < SCREEN_WIDTH:
                    screen.blit(img, rect)
                
        pygame.draw.polygon(screen, GRAY, [(left_arrow_rect.left + 5, left_arrow_rect.centery), (left_arrow_rect.right-5, left_arrow_rect.top+5), (left_arrow_rect.right-5, left_arrow_rect.bottom-5)])
        pygame.draw.polygon(screen, GRAY, [(right_arrow_rect.right - 5, right_arrow_rect.centery), (right_arrow_rect.left+5, right_arrow_rect.top+5), (right_arrow_rect.left+5, right_arrow_rect.bottom-5)])
        
        if all(puzzle_done_state.values()):
            if reset_button_image: 
                screen.blit(reset_button_image, reset_button_rect)
            else: 
                pygame.draw.rect(screen, BLUE, reset_button_rect)
            text = font.render(complete_text, True, RED)
            screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)))
        
        pygame.display.flip()
        
        # ★★★ Pygbag対応：重要な非同期処理 ★★★
        await asyncio.sleep(0)
        clock.tick(FPS)

    # ★★★ Pygbag対応：終了処理 ★★★
    pygame.quit()

# ★★★ Pygbag対応：メイン関数の実行 ★★★
if __name__ == "__main__":
    asyncio.run(main())