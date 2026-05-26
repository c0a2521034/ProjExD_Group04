import math
import os
import random
import sys
import pygame as pg

WIDTH = 450
HEIGHT = 800

# try...except は一切使用していません
os.chdir(os.path.dirname(os.path.abspath(__file__)))

STAGE_BORDER = (255, 215, 0)
LINE_COLOR = (255, 0, 0)
SS_LINE_COLOR = (255, 215, 0)
HP_TEXT_COLOR = (255, 50, 50)
TEXT_WHITE = (255, 255, 255)
BUTTON_COLOR = (50, 150, 250)
BUTTON_HOVER_COLOR = (80, 180, 255)
OBSTACLE_COLOR = (120, 120, 120)

class StrikeShotManager:
    """ストライクショット（SS）のデータ、ロジック、専用UIを管理するクラス。

    敵の撃破数をカウントし、規定数に達すると必殺技（SS）の発動可能フラグを立てる。
    また、画面左上に現在のチャージ状況や発動可能テキストを描画する。

    Attributes:
        requirement (int): SS発動に必要な敵の撃破数。
        killed_count (int): 現在のステージにおける敵の累計撃破数。
        is_ready (bool): SSが発動可能な状態かを表すフラグ。
        font (pg.font.Font): SS状況を画面に描画するためのフォントオブジェクト。
    """
    
    def __init__(self, requirement: int = 3) -> None:
        """StrikeShotManagerを初期化する。

        Args:
            requirement (int): SS発動に必要な撃破数。デフォルトは3。
        """
        self.requirement: int = requirement
        self.killed_count: int = 0
        self.is_ready: bool = False
        self.font: pg.font.Font = pg.font.SysFont("msgothic", 24)

    def reset(self) -> None:
        """SSのチャージカウントと発動可能フラグを初期状態にリセットする。

        ゲームオーバー時や、ステージクリアによるゲームリセット時に呼び出される。
        """
        self.killed_count = 0
        self.is_ready = False

    def charge(self) -> None:
        """撃破数を1増加させ、規定数に達していればSSを発動可能状態にする。

        敵のHPが0になり、ステージから削除されたタイミングで呼び出される。
        すでにSSが利用可能な状態（is_ready == True）の場合は何も行わない。
        """
        if not self.is_ready:
            self.killed_count += 1
            if self.killed_count >= self.requirement:
                self.is_ready = True

    def use(self) -> None:
        """SSの消費処理を行い、フラグと撃破カウンターをリセットする。

        プレイヤーがSS発動のためにショットを放った瞬間に呼び出される。
        """
        self.is_ready = False
        self.killed_count = 0

    def draw_status(self, screen: pg.Surface) -> None:
        """画面左上に現在のSSチャージ状況、または発動可能テキストを描画する。

        Args:
            screen (pg.Surface): 描画対象となるPygameのSurface（ウィンドウ画面）。
        """
        if self.is_ready:
            text: pg.Surface = self.font.render("★SS READY! (全員同時発射)", True, STAGE_BORDER)
        else:
            text = self.font.render(f"SSCharge: {self.killed_count}/{self.requirement}", True, TEXT_WHITE)
        screen.blit(text, (25, 25))


class Player:
    def __init__(self, x, y, image, size=60):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.is_moving = False
        self.image = image
        self.size = size

    @property
    def center(self):
        return (int(self.x + self.size // 2), int(self.y + self.size // 2))

    def launch(self, dx: float, dy: float, dist: float) -> None:
        FIXED_SPEED = 45
        self.vx = (dx / dist) * FIXED_SPEED
        self.vy = (dy / dist) * FIXED_SPEED
        self.is_moving = True

    def update_movement(self) -> None:
        if not self.is_moving:
            return

        self.x += self.vx
        if self.x < 10:
            self.x = 10
            self.vx *= -1
        elif self.x > WIDTH - 10 - self.size:
            self.x = WIDTH - 10 - self.size
            self.vx *= -1

        self.y += self.vy
        if self.y < 10:
            self.y = 10
            self.vy *= -1
        elif self.y > 600 - self.size:
            self.y = 600 - self.size
            self.vy *= -1

        self.vx *= 0.985
        self.vy *= 0.985

        if abs(self.vx) < 0.3 and abs(self.vy) < 0.3:
            self.is_moving = False
            self.vx = 0
            self.vy = 0

    def draw(self, screen: pg.Surface) -> None:
        screen.blit(self.image, (int(self.x), int(self.y)))


class Enemy:
    def __init__(self, x, y, enemy_type, image, size=70, hp=15):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.image = image
        self.size = size
        self.hp = hp

    def check_collision(self, player):
        if (self.x < player.x + player.size and
            player.x < self.x + self.size and
            self.y < player.y + player.size and
            player.y < self.y + self.size):

            # プレイヤー中心
            px = player.x + player.size / 2
            py = player.y + player.size / 2

            # 敵中心
            ex = self.x + self.size / 2
            ey = self.y + self.size / 2

            # 差分
            dx = px - ex
            dy = py - ey

            # 横方向の衝突が強い
            if abs(dx) > abs(dy):
                if dx > 0:
                    player.x = self.x + self.size
                else:
                    player.x = self.x - player.size

                player.vx *= -0.9

            # 縦方向の衝突が強い
            else:
                if dy > 0:
                    player.y = self.y + self.size
                else:
                    player.y = self.y - player.size

                player.vy *= -0.9

            self.hp -= 1
            return True

        return False

    def draw(self, screen, hp_font):
        screen.blit(self.image, (self.x, self.y))
        hp_text = hp_font.render(f"HP: {self.hp}", True, HP_TEXT_COLOR)
        screen.blit(hp_text, (self.x, self.y - 18))


class Obstacle:
    """
    プレイヤーの行く手を阻む障害物クラス（破壊は不可）
    x (float): 障害物の左上X座標
    y (float): 障害物の左上Y座標
    size (int): 障害物の一辺の長さ（正方形）
    """
    def __init__(self, x, y, size=60):
        self.x = x
        self.y = y
        self.size = size

    def check_collision(self, player):
        """
        プレイヤーとの衝突判定。敵の処理をベースにHP減少だけを除外
        プレイヤーキャラクターとの衝突判定を行い、
        衝突時にはプレイヤーの位置の押し戻しと速度の反転（バウンド）処理を行う
        この障害物は破壊不可
        衝突した場合は True、衝突していない場合は False
        """

    def check_collision(self, player: Player) -> bool:
        if (self.x < player.x + player.size and 
            player.x < self.x + self.size and
            self.y < player.y + player.size and 
            player.y < self.y + self.size):
            
            if player.vx > 0 and player.x + player.size - player.vx <= self.x:
                player.x = self.x - player.size
                player.vx *= -0.9
            elif player.vx < 0 and player.x - player.vx >= self.x + self.size:
                player.x = self.x + self.size
                player.vx *= -0.9

            if player.vy > 0 and player.y + player.size - player.vy <= self.y:
                player.y = self.y - player.size
                player.vy *= -0.9
            elif player.vy < 0 and player.y - player.vy >= self.y + self.size:
                player.y = self.y + self.size
                player.vy *= -0.9
                
            return True
        return False

    def draw(self, screen):
        """障害物の描画（今回はシンプルな四角形として描画。画像にする場合は blit に変更可能）"""
        pg.draw.rect(screen, OBSTACLE_COLOR, (self.x, self.y, self.size, self.size), border_radius=5)
        pg.draw.rect(screen, TEXT_WHITE, (self.x, self.y, self.size, self.size), 2, border_radius=5)
class BossEnemy(Enemy):
    """
    Bossクラスの追加。レーザーの描画調整、効果の追加。
    """
    def __init__(self, x, y, image):
        super().__init__(x, y, enemy_type="BOSS", image=image, size=120, hp=80)
        self.laser_cooldown = 0
        self.laser_counter = 0
        self.show_laser = False

        #  レーザー表示時間管理
        self.laser_timer = 0          # 現在の残り表示フレーム
        self.laser_duration = 30      # レーザー表示時間（例：30フレーム＝0.5秒）

    def fire_laser(self, players):
        hit = False
        cx = self.x + self.size // 2
        cy = self.y + self.size // 2

        for p in players: #レーザーのあたり安定の太さ
            px, py = p.center
            if abs(px - cx) < 40 or abs(py - cy) < 40: 
                hit = True

        return hit

    def draw_laser(self, screen):
        cx = self.x + self.size // 2
        cy = self.y + self.size // 2

        pg.draw.line(screen, (255, 0, 0), (0, cy), (WIDTH, cy), 40) #レーザーの見た目の太さ
        pg.draw.line(screen, (255, 0, 0), (cx, 0), (cx, HEIGHT), 40)

    #Bossの体力
    def draw(self, screen: pg.Surface, hp_font: pg.font.Font) -> None:
        screen.blit(self.image, (self.x, self.y))
        hp_text = hp_font.render(f"BOSS HP: {self.hp}", True, (255, 80, 80))
        screen.blit(hp_text, (self.x, self.y - 25))


class item:
    """
    アイテムに関してのクラス(追加機能)
    """
    def __init__(self, image, x, y):
        self.image = image
        self.x = x
        self.y = y
        self.is_used = False
    
    def use(self, game_instance):
        """アイテムを使用し、ゲームのターン数を1増やす"""
        if not self.is_used:
            game_instance.left_turns += 1
            self.is_used = True
            return True
        return False
    
    def draw(self, screen):
        """未使用の場合のみ画面に描画"""
        if not self.is_used:
            screen.blit(self.image, (self.x, self.y))
    
        


class Bullet:
    """味方から発射される十字弾のクラス"""
    def __init__(self, x, y, vx, vy, size=20):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        # 【多段ヒット防止用】この弾が既にダメージを与えた敵を記録する集合(Set)
        # 貫通弾が敵の矩形を通り過ぎる間、毎フレームダメージが入るのを防ぎます
        self.damaged_enemies = set()

    def update(self):
        """弾を毎フレーム、設定された速度ぶん移動させる"""
        self.x += self.vx
        self.y += self.vy

    def is_offscreen(self):
        """弾が上下左右の画面外へ完全に消え去ったかを判定する"""
        return (self.x < -50 or self.x > WIDTH + 50 or
                self.y < -50 or self.y > HEIGHT + 50)

    def draw(self, screen):
        # 水色の円で貫通弾を描画します
        pg.draw.circle(screen, (0, 255, 255), (int(self.x), int(self.y)), self.size // 2)


class GameUI:
    def __init__(self):
        self.bg_img = pg.transform.scale(pg.image.load("haikei1.png").convert_alpha(), (WIDTH, HEIGHT))
        self.ui_bg_img = pg.transform.scale(pg.image.load("haikei2.png").convert_alpha(), (WIDTH - 30, 185))
        self.start_bg_img = pg.transform.scale(pg.image.load("haikei1.png").convert_alpha(), (WIDTH, HEIGHT))

        self.hp_font = pg.font.SysFont(None, 20)
        self.turn_font = pg.font.SysFont(None, 40)
        self.result_font = pg.font.SysFont(None, 60)
        self.title_font = pg.font.SysFont("msgothic", 50)
        self.button_font = pg.font.SysFont(None, 40)
        self.sub_font = pg.font.SysFont(None, 25)

    def draw_start_screen(self, screen, button_rect):
        screen.blit(self.start_bg_img, (0, 0))
        
        title_text = self.title_font.render("ヤマダストライク", True, STAGE_BORDER)

    def draw_start_screen(self, screen: pg.Surface, button_rect: pg.Rect) -> None:
        screen.blit(self.start_bg_img, (0, 0))
        title_text = self.title_font.render("ヤマダストライク", True, STAGE_BORDER)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(title_text, title_rect)

        mouse_pos = pg.mouse.get_pos()
        color = BUTTON_HOVER_COLOR if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pg.draw.rect(screen, color, button_rect, border_radius=10)
        pg.draw.rect(screen, TEXT_WHITE, button_rect, 3, border_radius=10)

        btn_text = self.button_font.render("START", True, TEXT_WHITE)
        btn_text_rect = btn_text.get_rect(center=button_rect.center)
        screen.blit(btn_text, btn_text_rect)

    def draw_base_layer(self, screen: pg.Surface) -> None:
        screen.blit(self.bg_img, (0, 0))
        pg.draw.rect(screen, STAGE_BORDER, (10, 10, WIDTH - 20, HEIGHT - 20), 4)
        screen.blit(self.ui_bg_img, (15, 600))
        pg.draw.line(screen, STAGE_BORDER, (10, 600), (WIDTH - 10, 600), 4)

    def draw_bottom_ui_icons(self, screen: pg.Surface, chara_images: list, current_turn: int, anyone_moving: bool, game_state: str, ss_ready: bool) -> None:
        """画面下のキャラクターアイコン群の描画を行います。
        
        SSが準備できている（ss_ready=True）ときは、手番に関わらずすべてのアイコンを金枠で囲います。
        """
        for i in range(3):
            x = 80 + i * 110
            y = 630
            screen.blit(chara_images[i], (x, y))
            
            if ss_ready and game_state == "PLAY":
                pg.draw.rect(screen, SS_LINE_COLOR, (x - 4, y - 4, 68, 68), 3)
            elif i == current_turn and not anyone_moving and game_state == "PLAY":
                pg.draw.rect(screen, STAGE_BORDER, (x - 4, y - 4, 68, 68), 3)

    def draw_guide_line(self, screen: pg.Surface, start_pos: tuple, end_pos: tuple, is_ss: bool) -> None:
        """引っ張り中のガイド線を描画します。
        
        SS発動時（is_ss=True）は、通常よりも太い金色の線でガイド線を描画します。
        """
        color = SS_LINE_COLOR if is_ss else LINE_COLOR
        pg.draw.line(screen, color, start_pos, end_pos, 4 if is_ss else 3)

    def draw_turn_count(self, screen: pg.Surface, left_turns: int) -> None:
        turn_text = self.turn_font.render(f"TURN: {left_turns}", True, TEXT_WHITE)
        screen.blit(turn_text, (WIDTH - 140, 25))

    def draw_result_screen(self, screen: pg.Surface, game_state: str) -> None:
        if game_state == "PLAY" or game_state == "START":
            return

        mask = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        mask.fill((0, 0, 0, 150))
        screen.blit(mask, (0, 0))

        if game_state == "GAMEOVER":
            text = self.result_font.render("GAME OVER", True, (255, 0, 0))
        else:
            text = self.result_font.render("STAGE CLEAR!", True, (0, 255, 0))

        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(text, text_rect)

        sub_text = self.sub_font.render("CLICK ANYWHERE TO RETURN TO TITLE", True, TEXT_WHITE)
        sub_rect = sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
        screen.blit(sub_text, sub_rect)


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("超簡易版モンスト(Class版)")
        self.clock = pg.time.Clock()

        self.ui = GameUI()
        self.start_button_rect = pg.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 60)

        self.chara_images = [
            pg.transform.scale(pg.image.load("chara1.jpg").convert_alpha(), (60, 60)),
            pg.transform.scale(pg.image.load("chara2.jpg").convert_alpha(), (60, 60)),
            pg.transform.scale(pg.image.load("chara3.png").convert_alpha(), (60, 60))
        ]
        self.enemy_images: list = [
            pg.transform.scale(pg.image.load("enemy1.png").convert_alpha(), (70, 70)),
            pg.transform.scale(pg.image.load("enemy1.png").convert_alpha(), (70, 70)),
            pg.transform.scale(pg.image.load("enemy1.png").convert_alpha(), (70, 70))
        ]

        # ★★★ ボス画像読み込み ★★★
        self.boss_image = pg.transform.scale(pg.image.load("boss.png").convert_alpha(), (120, 120))

        # 追加機能変更点アイテム画像の読み込み 
        self.item_image = pg.transform.scale(pg.image.load("item.jpeg").convert_alpha(), (50, 50))
        self.ss_manager = StrikeShotManager()
        self.game_state = "START"
        self.running = True
        self.reset_game()

    def reset_game(self):
        self.players = [
            Player(120, 450, self.chara_images[0]),
            Player(195, 480, self.chara_images[1]),
            Player(270, 450, self.chara_images[2])
        ]
        self.enemies = []
        self._spawn_enemies()
        self.obstacles = []
        self.turn_counter = 0

        # ★★★ ボスを中央に配置 ★★★
        boss_x = WIDTH // 2 - 60
        boss_y = 200
        self.enemies.append(BossEnemy(boss_x, boss_y, self.boss_image))

        # 追加機能変更点　ゲームリセット時にアイテムのインスタンスを作成（画面右下に位置するように）
        self.game_item = item(self.item_image, 380, 645)
        
        self.bullets = []  # 画面上の弾のリスト
        self.triggered_allies = set()  # 友情発動済み
        self.touching_allies = set()   # 接触中の味方ペア
        
        self.current_turn: int = 0
        self.is_dragging: bool = False
        self.left_turns: int = 9

        self.turn_processed = False
        
        # --- マネージャーの初期化 ---
        self.ss_manager.reset()

    def _spawn_enemies(self) -> None:
        num_enemies = random.randint(3, 5)
        for _ in range(num_enemies):
            enemy_type = random.randint(0, 2)
            x = random.randint(30, WIDTH - 100)
            y = random.randint(50, 450)
            img = self.enemy_images[enemy_type]
            self.enemies.append(Enemy(x, y, enemy_type, img, hp=5))

    def _spawn_obstacle(self):
        """ランダムな位置に障害物を1つ生成する"""
        x = random.randint(30, WIDTH - 80)
        y = random.randint(50, 450)
        self.obstacles.append(Obstacle(x, y))
    def spawn_cross_bullets(self, ally):
        """味方の中心から上下左右に弾を発射する"""
        cx, cy = ally.center
        speed = 12.0  # 弾の速度
        
        self.bullets.append(Bullet(cx, cy, 0, -speed))  # 上
        self.bullets.append(Bullet(cx, cy, 0, speed))   # 下
        self.bullets.append(Bullet(cx, cy, -speed, 0))  # 左
        self.bullets.append(Bullet(cx, cy, speed, 0))   # 右

    def handle_events(self):
        mouse_pos = pg.mouse.get_pos()

    def handle_events(self) -> None:
        mouse_pos: tuple = pg.mouse.get_pos()
        p = self.players[self.current_turn] if self.game_state == "PLAY" else None
        anyone_moving: bool = any(pl.is_moving for pl in self.players)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

            
            if self.game_state == "START":
                if event.type == pg.MOUSEBUTTONDOWN:
                    if self.start_button_rect.collidepoint(mouse_pos):
                        self.game_state = "PLAY"

            elif self.game_state == "PLAY":
                # 追加機能変更点スペースキーが押されたらアイテムを使う
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_SPACE:
                        self.game_item.use(self)

                # 引っ張り開始判定
                if event.type == pg.MOUSEBUTTONDOWN and not anyone_moving:
                    # --- SS READY時は、どのキャラクターを触っても選択（引っ張り）可能にする ---
                    if self.ss_manager.is_ready:
                        for idx, pl in enumerate(self.players):
                            if pl.x <= mouse_pos[0] <= pl.x + pl.size and pl.y <= mouse_pos[1] <= pl.y + pl.size:
                                self.current_turn = idx
                                self.is_dragging = True
                                break
                    else:
                        if p and p.x <= mouse_pos[0] <= p.x + p.size and p.y <= mouse_pos[1] <= p.y + p.size:
                            self.is_dragging = True

                if event.type == pg.MOUSEBUTTONUP and self.is_dragging:
                    self.is_dragging = False

                    p_active: Player = self.players[self.current_turn]
                    p_center: tuple = p_active.center

                    dx: float = p_center[0] - mouse_pos[0]
                    dy: float = p_center[1] - mouse_pos[1]
                    dist: float = math.hypot(dx, dy)

                    if dist > 5:
                        self.triggered_allies.clear()

                        if self.ss_manager.is_ready:
                            for pl in self.players:
                                pl.launch(dx, dy, dist)
                            self.ss_manager.use()
                        else:
                            p_active.launch(dx, dy, dist)

                        self.current_turn = (self.current_turn + 1) % 3
                        self.turn_processed = False

            elif self.game_state in ("GAMEOVER", "CLEAR"):
                if event.type == pg.MOUSEBUTTONDOWN:
                    self.reset_game()
                    self.game_state = "START"

        # 全プレイヤーの移動更新と敵・味方との衝突判定
    def update(self) -> None:
        if self.game_state != "PLAY":
            return
        
        for player in self.players:

            was_moving = player.is_moving

            player.update_movement()
            
            # 移動中なら当たり判定をチェック
            if player.is_moving:
                # 敵との衝突判定
                for enemy in list(self.enemies):
                    if enemy.check_collision(player):
                        if enemy.hp <= 0:
                            self.enemies.remove(enemy)
                            self.ss_manager.charge()
                for obstacle in self.obstacles:
                    obstacle.check_collision(player)
                
                # 味方との衝突判定（友情コンボの発動）
                for ally in self.players:
                    if player == ally:
                        continue

                    pair = (id(player), id(ally))

                    is_colliding = (
                        player.x < ally.x + ally.size and
                        player.x + player.size > ally.x and
                        player.y < ally.y + ally.size and
                        player.y + player.size > ally.y
                    )

                    # 接触開始時だけ友情発動
                    if is_colliding:
                        if pair not in self.touching_allies:
                            self.touching_allies.add(pair)

                            if ally not in self.triggered_allies:
                                self.triggered_allies.add(ally)
                                self.spawn_cross_bullets(ally)

                        if is_colliding:
                            if pair not in self.touching_allies:
                                self.touching_allies.add(pair)

                                if ally not in self.triggered_allies:
                                    self.triggered_allies.add(ally)
                                    self.spawn_cross_bullets(ally)

                        else:
                            if pair in self.touching_allies:
                                self.touching_allies.remove(pair)

            # 全員停止した瞬間に1回だけターン処理
            if (
                was_moving
                and not player.is_moving
                and not any(pl.is_moving for pl in self.players)
                and not self.turn_processed
            ):

                self.turn_processed = True

                # ターン進行
                self.left_turns -= 1
                self.turn_counter += 1

                # 3ターンごとにブロック生成
                if self.turn_counter >= 3:
                    self._spawn_obstacle()
                    self.turn_counter = 0

                # ボスのレーザー処理
                for enemy in self.enemies:
                    if enemy.type == "BOSS":

                        enemy.laser_counter += 1

                        if enemy.laser_counter % 2 == 0:
                            enemy.show_laser = True
                            enemy.laser_timer = enemy.laser_duration

                            if enemy.fire_laser(self.players):
                                self.left_turns -= 1
                        else:
                            enemy.show_laser = False

                # ゲームオーバー判定
                if self.left_turns <= 0:
                    self.game_state = "GAMEOVER"

        # 弾の移動と敵との衝突判定
        for b in list(self.bullets):
            b.update()
            
            # 画面外に出たらリストから削除
            if b.is_offscreen():
                self.bullets.remove(b)
                continue
                
            # 弾と敵の当たり判定（貫通仕様）
            b_size = b.size
            bx = b.x - b_size / 2
            by = b.y - b_size / 2
            for enemy in list(self.enemies):
                if (bx < enemy.x + enemy.size and bx + b_size > enemy.x and
                    by < enemy.y + enemy.size and by + b_size > enemy.y):
                    
                    # この弾がまだこの敵に当たっていなければダメージを与えて記憶
                    if enemy not in b.damaged_enemies:
                        enemy.hp -= 5  # 弾のダメージ（5ダメージに変更しました）
                        b.damaged_enemies.add(enemy)
                        if enemy.hp <= 0 and enemy in self.enemies:
                            self.enemies.remove(enemy)
                            self.ss_manager.charge()

        # ★★★ レーザー表示時間のカウントダウン ★★★
        for enemy in self.enemies:
            if enemy.type == "BOSS":
                if enemy.laser_timer > 0:
                    enemy.laser_timer -= 1
                else:
                    enemy.show_laser = False

        # ★ ボス撃破でクリア
        boss_alive = any(e.type == "BOSS" for e in self.enemies)
        if not boss_alive:
            self.game_state = "CLEAR"

    def draw(self) -> None:
        if self.game_state == "START":
            self.ui.draw_start_screen(self.screen, self.start_button_rect)
        else:
            self.ui.draw_base_layer(self.screen)

            # 敵描画
            for enemy in self.enemies:
                enemy.draw(self.screen, self.ui.hp_font)
            
            for obstacle in self.obstacles:
                obstacle.draw(self.screen)

            # ★★★ レーザー描画（laser_timer > 0 の間だけ） ★★★
            for enemy in self.enemies:
                if enemy.type == "BOSS" and enemy.show_laser:
                    enemy.draw_laser(self.screen)

            anyone_moving = any(pl.is_moving for pl in self.players)
                
            anyone_moving: bool = any(pl.is_moving for pl in self.players)
            
            # --- 引数追加: ss_manager.is_ready を渡し、アイコンの金枠描画を切り替える ---
            self.ui.draw_bottom_ui_icons(
                self.screen, self.chara_images, self.current_turn, anyone_moving, self.game_state, self.ss_manager.is_ready
            )

            # 追加機能変更点　アイテムを画面に描画（UIレイヤーの上、プレイヤーの下あたり）
            self.game_item.draw(self.screen)
            
            for player in self.players:
                player.draw(self.screen)

                
            # 画面上の弾を描画
            for b in self.bullets:
                b.draw(self.screen)
                
            if self.is_dragging and self.game_state == "PLAY":
                p = self.players[self.current_turn]

                p: Player = self.players[self.current_turn]
                # --- 引数追加: ガイド線を金色にするかの判定用フラグを渡す ---
                self.ui.draw_guide_line(self.screen, p.center, pg.mouse.get_pos(), self.ss_manager.is_ready)
                
            self.ui.draw_turn_count(self.screen, self.left_turns)
            
            # --- 追加: SSマネージャー専用のステータス描画メソッドを呼ぶ ---
            self.ss_manager.draw_status(self.screen)
            
            self.ui.draw_result_screen(self.screen, self.game_state)

        pg.display.flip()

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pg.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()