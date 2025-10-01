import asyncio
import random
import os
import webbrowser
import pygame

# --- 定数設定 ---
# 画面設定
SCREEN_WIDTH, SCREEN_HEIGHT = 300, 500
FPS = 60
ASSETS_PATH = "assets"

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
LINK_COLOR = (100, 100, 255)

# ゲーム設定
BACKGROUND_SIZE = (250, 350)
BASE_PIECE_HEIGHT = 45
CONTINUOUS_SCROLL_SPEED = 5
PIECE_SNAP_DISTANCE = 35

# --- ヘルパー関数 ---

def draw_text(screen, text, font, color, pos, is_center=True):
    """画面にテキストを描画する"""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=pos) if is_center else text_surface.get_rect(topleft=pos)
    screen.blit(text_surface, text_rect)

# --- アセット読み込み ---

def load_fonts():
    """フォントを読み込む"""
    try:
        font_path = os.path.join(ASSETS_PATH, "NotoSansJP-Bold.ttf")
        return {
            "jp_40": pygame.font.Font(font_path, 40),
            "jp_36": pygame.font.Font(font_path, 36),
            "default_24": pygame.font.Font(None, 24),
            "default_18": pygame.font.Font(None, 18),
        }
    except pygame.error:
        print("日本語フォントの読み込みに失敗しました。代替フォントを使用します。")
        return {
            "jp_40": pygame.font.Font(None, 60),
            "jp_36": pygame.font.Font(None, 50),
            "default_24": pygame.font.Font(None, 24),
            "default_18": pygame.font.Font(None, 18),
        }

def load_images(piece_data):
    """画像アセットを読み込んでリサイズする"""
    images = {"pieces": {}, "frames": {}}
    
    # 全ピースの画像を読み込み
    all_piece_names = piece_data["original_pieces"] + ["unchi.png"]
    for name in all_piece_names:
        try:
            path = os.path.join(ASSETS_PATH, name)
            original_image = pygame.image.load(path).convert_alpha()
            
            if name == "unchi.png":
                final_image = pygame.transform.scale(original_image, (50, 50))
            else:
                multiplier = piece_data["scale_multipliers"].get(name, 1.0)
                angle = piece_data["rotations"].get(name, 0)
                
                target_h = BASE_PIECE_HEIGHT * multiplier
                w, h = original_image.get_size()
                aspect = w / h if h > 0 else 1
                new_w, new_h = int(target_h * aspect), int(target_h)
                
                resized_image = pygame.transform.scale(original_image, (new_w, new_h))
                final_image = pygame.transform.rotate(resized_image, angle)
            
            images["pieces"][name] = final_image
            if name != "unchi.png":
                images["frames"][name] = pygame.Surface(final_image.get_size(), pygame.SRCALPHA)
        except pygame.error:
            print(f"画像の読み込みに失敗: {name}")
            images["pieces"][name] = pygame.Surface((50, 50), pygame.SRCALPHA)

    # 背景・UI画像を読み込み
    try:
        images["background"] = pygame.transform.scale(
            pygame.image.load(os.path.join(ASSETS_PATH, "human.png")).convert_alpha(), BACKGROUND_SIZE
        )
        images["reset_button"] = pygame.transform.scale(
            pygame.image.load(os.path.join(ASSETS_PATH, "reset.png")).convert_alpha(), (55, 30)
        )
        images["github_icon"] = pygame.transform.scale(
            pygame.image.load(os.path.join(ASSETS_PATH, "github_icon.png")).convert_alpha(), (30, 30)
        )
    except pygame.error as e:
        print(f"UI画像の読み込みに失敗: {e}")
        # フォールバック用のダミー画像を準備
        images["background"] = pygame.Surface(BACKGROUND_SIZE)
        images["reset_button"] = pygame.Surface((55, 30))
        images["github_icon"] = pygame.Surface((30, 30))


    return images

# --- ゲーム状態管理 ---

class GameState:
    """ゲームの状態を管理するクラス"""
    def __init__(self):
        self.game_level = 1
        self.reset_count = 0
        self.dragging_piece = None
        self.swiping_slider = False
        self.scrolling_left = False
        self.scrolling_right = False
        self.swipe_start_x = 0
        self.initial_scroll_x = 0
        self.scroll_x = 0
        self.total_pieces_width = 1

        self.piece_names = []
        self.piece_start_positions = {}
        self.current_piece_positions = {}
        self.puzzle_done_state = {}

    def reset_for_level1(self, piece_data, ui_elements):
        """レベル1用にゲーム状態をリセット"""
        self.game_level = 1
        self.piece_names = list(piece_data["original_pieces"])
        random.shuffle(self.piece_names)
        
        start_x = ui_elements["spacing_x"]
        self.piece_start_positions = {
            name: [start_x + i * ui_elements["spacing_x"], ui_elements["slider_y"]]
            for i, name in enumerate(self.piece_names)
        }
        self.current_piece_positions = self.piece_start_positions.copy()
        self.puzzle_done_state = {name: False for name in piece_data["original_pieces"]}
        self.scroll_x = 0
        self.total_pieces_width = len(self.piece_names) * ui_elements["spacing_x"]
        if self.total_pieces_width == 0:
            self.total_pieces_width = 1

    def transition_to_level2(self, ui_elements):
        """レベル2へ移行"""
        self.game_level = 2
        self.piece_names = ["unchi.png"]
        start_pos_x = SCREEN_WIDTH // 2
        
        self.piece_start_positions = {"unchi.png": [start_pos_x, ui_elements["slider_y"]]}
        self.current_piece_positions["unchi.png"] = [start_pos_x, ui_elements["slider_y"]]
        self.puzzle_done_state["unchi.png"] = False
        self.scroll_x = 0
        self.total_pieces_width = 1
        
# --- メインゲームロジック ---

async def main():
    # Pygameの初期化
    pygame.font.init()
    pygame.display.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ほねほねパズル")
    clock = pygame.time.Clock()

    # --- アセットとデータの準備 ---
    fonts = load_fonts()
    
    background_pos = (
        SCREEN_WIDTH // 2 - BACKGROUND_SIZE[0] // 2, 
        SCREEN_HEIGHT // 2 - BACKGROUND_SIZE[1] // 2 - 70
    )

    piece_data = {
        "original_pieces": [
            "backbone.png", "costa.png", "pelvis.png", "right_femur.png", "left_femur.png",
            "right_leg.png", "left_leg.png", "right_arm.png", "left_arm.png", "head.png",
            "right_knee.png", "left_knee.png"
        ],
        "positions": {
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
        },
        "scale_multipliers": {
            "head.png": 1.12, "backbone.png": 2.8, "costa.png": 1.25, "pelvis.png": 1.15,
            "right_arm.png": 3.3, "left_arm.png": 3.3, "right_femur.png": 1.76,
            "left_femur.png": 1.76, "right_knee.png": 0.42, "left_knee.png": 0.42,
            "right_leg.png": 2.28, "left_leg.png": 2.28
        },
        "rotations": {"right_arm.png": -9.4, "left_arm.png": 9.4},
        "drag_inflations": {"default": 20, "right_knee.png": 40, "left_knee.png": 40}
    }
    
    images = load_images(piece_data)
    
    pelvis_center = piece_data["positions"]["pelvis.png"]
    unchi_target_pos = (pelvis_center[0], pelvis_center[1] + 60) # Y座標を調整

    # --- UI要素の準備 ---
    slider_y = 440
    spacing_x = int(BASE_PIECE_HEIGHT * 2.4)
    ui_elements = {
        "slider_y": slider_y,
        "spacing_x": spacing_x,
        "slider_area": pygame.Rect(0, slider_y - 40, SCREEN_WIDTH, 100),
        "reset_button_rect": pygame.Rect(SCREEN_WIDTH - 65, 10, 55, 30),
        "left_arrow_rect": pygame.Rect(5, slider_y - 20, 30, 40),
        "right_arrow_rect": pygame.Rect(SCREEN_WIDTH - 35, slider_y - 20, 30, 40),
        "license_rect": pygame.Rect(5, 5, 0, 0),
        "github_icon_rect": pygame.Rect(5, 28, 30, 30),
        "license_url": "https://github.com/ko-sekishinkai/bone_puzzle/blob/main/LICENSE",
        "github_url": "https://github.com/ko-sekishinkai/bone_puzzle",
        "congrats_text": fonts["jp_36"].render("おめでとう！", True, RED)
    }
    license_text_normal = fonts["default_18"].render("MIT License", True, GRAY)
    license_text_hover = fonts["default_18"].render("MIT License", True, LINK_COLOR)
    ui_elements["license_rect"] = license_text_normal.get_rect(topleft=(5, 5))

    # --- タイトル表示 ---
    screen.fill(WHITE)
    draw_text(screen, "ほねほねパズル", fonts["jp_40"], BLACK, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    pygame.display.flip()
    await asyncio.sleep(2.5)

    # --- ゲームループの初期化 ---
    state = GameState()
    state.reset_for_level1(piece_data, ui_elements)
    running = True

    while running:
        # --- 1. イベント処理 ---
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # マウスボタン押下処理
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ui_elements["license_rect"].collidepoint(mouse_pos):
                    webbrowser.open(ui_elements["license_url"])
                    continue
                if ui_elements["github_icon_rect"].collidepoint(mouse_pos):
                    webbrowser.open(ui_elements["github_url"])
                    continue
                if state.game_level == 2 and state.puzzle_done_state.get("unchi.png") and \
                   ui_elements["reset_button_rect"].collidepoint(mouse_pos):
                    state.reset_count += 1
                    state.reset_for_level1(piece_data, ui_elements)
                    continue

                if ui_elements["left_arrow_rect"].collidepoint(mouse_pos):
                    state.scrolling_left = True
                elif ui_elements["right_arrow_rect"].collidepoint(mouse_pos):
                    state.scrolling_right = True
                elif ui_elements["slider_area"].collidepoint(mouse_pos):
                    piece_clicked = False
                    for name in reversed(state.piece_names):
                        if not state.puzzle_done_state.get(name):
                            offsets = [0, state.total_pieces_width, -state.total_pieces_width] if state.game_level == 1 else [0]
                            for offset in offsets:
                                on_screen_x = state.piece_start_positions[name][0] - state.scroll_x + offset
                                piece_rect = images["pieces"][name].get_rect(center=(on_screen_x, slider_y))
                                
                                inflation = piece_data["drag_inflations"].get(name, piece_data["drag_inflations"]["default"])
                                if piece_rect.inflate(inflation, inflation).collidepoint(mouse_pos):
                                    state.dragging_piece = name
                                    state.current_piece_positions[name] = list(mouse_pos)
                                    piece_clicked = True
                                    break
                        if piece_clicked:
                            break
                    if not piece_clicked:
                        state.swiping_slider = True
                        state.swipe_start_x = mouse_pos[0]
                        state.initial_scroll_x = state.scroll_x

            # マウスボタン解放処理
            if event.type == pygame.MOUSEBUTTONUP:
                state.scrolling_left = False
                state.scrolling_right = False
                state.swiping_slider = False
                
                if state.dragging_piece:
                    piece_name = state.dragging_piece
                    target_pos = unchi_target_pos if piece_name == "unchi.png" else piece_data["positions"][piece_name]
                    
                    dist = pygame.math.Vector2(state.current_piece_positions[piece_name]).distance_to(target_pos)
                    if dist <= PIECE_SNAP_DISTANCE:
                        state.current_piece_positions[piece_name] = list(target_pos)
                        state.puzzle_done_state[piece_name] = True
                    
                    state.dragging_piece = None
            
            # マウス移動処理
            if event.type == pygame.MOUSEMOTION:
                if state.dragging_piece:
                    state.current_piece_positions[state.dragging_piece] = list(event.pos)
                elif state.swiping_slider:
                    swipe_dist = state.swipe_start_x - event.pos[0]
                    if state.game_level == 1:
                        state.scroll_x = (state.initial_scroll_x + swipe_dist) % state.total_pieces_width
                    else:
                        state.scroll_x = max(0, min(0, state.initial_scroll_x + swipe_dist))

        # --- 2. 状態更新 ---
        # 左右ボタン長押しによるスクロール
        if state.scrolling_left:
            state.scroll_x = (state.scroll_x - CONTINUOUS_SCROLL_SPEED) % state.total_pieces_width
        if state.scrolling_right:
            state.scroll_x = (state.scroll_x + CONTINUOUS_SCROLL_SPEED) % state.total_pieces_width

        # レベルクリア判定
        is_level1_complete = all(state.puzzle_done_state.get(name, False) for name in piece_data["original_pieces"])
        if state.game_level == 1 and is_level1_complete:
            state.transition_to_level2(ui_elements)

        # --- 3. 描画処理 ---
        screen.fill(WHITE)
        screen.blit(images["background"], background_pos)

        # ピースの配置枠を描画 (レベル1のみ)
        if state.game_level == 1:
            for name, pos in piece_data["positions"].items():
                if not state.puzzle_done_state.get(name):
                    frame_img = images["frames"][name]
                    screen.blit(frame_img, frame_img.get_rect(center=pos))

        # 配置済みピースとドラッグ中ピースを描画
        all_pieces_to_draw = piece_data["original_pieces"] + ["unchi.png"]
        for name in all_pieces_to_draw:
            if state.puzzle_done_state.get(name) or name == state.dragging_piece:
                img = images["pieces"].get(name)
                pos = state.current_piece_positions.get(name)
                if img and pos:
                    screen.blit(img, img.get_rect(center=pos))

        # 下部スライダーのピースを描画
        for name in state.piece_names:
            if not state.puzzle_done_state.get(name) and name != state.dragging_piece:
                img = images["pieces"][name]
                offsets = [0, state.total_pieces_width, -state.total_pieces_width] if state.game_level == 1 else [0]
                for offset in offsets:
                    on_screen_x = state.piece_start_positions[name][0] - state.scroll_x + offset
                    rect = img.get_rect(center=(int(on_screen_x), slider_y))
                    if rect.right > 0 and rect.left < SCREEN_WIDTH:
                        screen.blit(img, rect)
        
        # UI要素の描画
        # 左右矢印
        if state.game_level == 1:
            pygame.draw.polygon(screen, GRAY, [
                (ui_elements["left_arrow_rect"].left + 5, ui_elements["left_arrow_rect"].centery),
                (ui_elements["left_arrow_rect"].right - 5, ui_elements["left_arrow_rect"].top + 5),
                (ui_elements["left_arrow_rect"].right - 5, ui_elements["left_arrow_rect"].bottom - 5)
            ])
            pygame.draw.polygon(screen, GRAY, [
                (ui_elements["right_arrow_rect"].right - 5, ui_elements["right_arrow_rect"].centery),
                (ui_elements["right_arrow_rect"].left + 5, ui_elements["right_arrow_rect"].top + 5),
                (ui_elements["right_arrow_rect"].left + 5, ui_elements["right_arrow_rect"].bottom - 5)
            ])
        
        # クリア後メッセージとリセットボタン
        if state.game_level == 2 and state.puzzle_done_state.get("unchi.png"):
            congrats_rect = ui_elements["congrats_text"].get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
            screen.blit(ui_elements["congrats_text"], congrats_rect)
            screen.blit(images["reset_button"], ui_elements["reset_button_rect"])

        # リセット回数
        reset_rect = ui_elements["reset_button_rect"]
        draw_text(screen, f"Resets: {state.reset_count}", fonts["default_24"], BLACK,
                  (reset_rect.centerx, reset_rect.bottom + 15))
        
        # ライセンスとGitHubリンク
        is_hovering_license = ui_elements["license_rect"].collidepoint(mouse_pos)
        is_hovering_github = ui_elements["github_icon_rect"].collidepoint(mouse_pos)
        pygame.mouse.set_cursor(
            pygame.SYSTEM_CURSOR_HAND if is_hovering_license or is_hovering_github else pygame.SYSTEM_CURSOR_ARROW
        )
        screen.blit(license_text_hover if is_hovering_license else license_text_normal, ui_elements["license_rect"])
        screen.blit(images["github_icon"], ui_elements["github_icon_rect"])

        # 画面更新
        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(FPS)

if __name__ == "__main__":
    # スクリプトのディレクトリをワーキングディレクトリに設定
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(main())