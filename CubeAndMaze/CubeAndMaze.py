import pyxel

GAME_TITLE = "CUBE AND MAZE"
PYXRES_NAME = "CubeAndMaze.pyxres"
TEXT_COLOR_1 = 1
TEXT_COLOR_2 = 7
TRANSPARENT_COLOR = 0
TILE_PX = 8
WIDTH_TILE = 16
HEIGHT_TILE = 16
WIDTH_PX = WIDTH_TILE * TILE_PX
HEIGHT_PX = HEIGHT_TILE * TILE_PX
TILE_HALF = TILE_PX // 2
END_ROOM = (15, 7, 0)
INIT_X_TILE = 7
INIT_Y_TILE = 222
INIT_Z = 0

player = None
blocks = []
enemies = []
chests = []
chests_pos = []

def is_up() -> bool:
    return pyxel.btnp(pyxel.KEY_UP) \
        or pyxel.btnp(pyxel.KEY_W) \
        or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP)

def is_left() -> bool:
    return pyxel.btn(pyxel.KEY_LEFT) \
        or pyxel.btn(pyxel.KEY_A) \
        or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)

def is_down() -> bool:
    return pyxel.btnp(pyxel.KEY_DOWN) \
        or pyxel.btnp(pyxel.KEY_S) \
        or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)

def is_right() -> bool:
    return pyxel.btn(pyxel.KEY_RIGHT) \
        or pyxel.btn(pyxel.KEY_D) \
        or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)

def is_decided() -> bool:
    return pyxel.btnp(pyxel.KEY_Z) \
        or pyxel.btnp(pyxel.KEY_SPACE) \
        or pyxel.btnp(pyxel.KEY_RETURN) \
        or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A) \
        or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B) \
        or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X) \
        or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_Y)

class Mob:
    top    = 0
    bottom = 7
    left   = 0
    right  = 7
    u = TILE_PX
    v = 0
    wall_id = 1

    def __init__(self, x_tile: int , y_tile: int) -> None:
        self.x = TILE_PX * x_tile
        self.y = TILE_PX * y_tile
        self.dx = 0
        self.dy = 0

    def detect_collision(self, dx: int, dy: int) -> bool:
        next_left   = self.x + dx + self.__class__.left
        next_right  = self.x + dx + self.__class__.right
        next_top    = self.y + dy + self.__class__.top
        next_bottom = self.y + dy + self.__class__.bottom
        return max(
            get_wall_id(next_left,  next_top),
            get_wall_id(next_left,  next_bottom),
            get_wall_id(next_right, next_top),
            get_wall_id(next_right, next_bottom)
        ) >= self.__class__.wall_id

    def detect_mob(self, dx: int, dy: int, mob) -> bool:
        x_next = self.x + dx
        y_next = self.y + dy
        return  x_next + self.__class__.left   <= mob.x + mob.__class__.right \
            and x_next + self.__class__.right  >= mob.x + mob.__class__.left \
            and y_next + self.__class__.top    <= mob.y + mob.__class__.bottom \
            and y_next + self.__class__.bottom >= mob.y + mob.__class__.top

    def update(self) -> None:
        abs_dx = abs(self.dx)
        abs_dy = abs(self.dy)
        sign_dx = 1 if self.dx > 0 else -1
        sign_dy = 1 if self.dy > 0 else -1
        for _ in range(abs_dx):
            if self.detect_collision(sign_dx, 0):
                break
            self.x += sign_dx
        for _ in range(abs_dy):
            if self.detect_collision(0, sign_dy):
                break
            self.y += sign_dy

    def draw(self) -> None:
        pyxel.blt(
            self.x, self.y, 0, self.__class__.u, self.__class__.v,
            TILE_PX, TILE_PX, TRANSPARENT_COLOR)

class Player(Mob):
    top    = 2
    bottom = 7
    left   = 1
    right  = 6
    wall_id = 2

    def __init__(self, x_tile: int, y_tile: int, z: int) -> None:
        super().__init__(x_tile, y_tile)
        self.z = z
        self.is_on_floor = False
        self.is_right = True
        self.is_dead = False

    def respawn(self, x: int, y: int, z: int) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.dx = 0
        self.dy = 0
        self.is_dead = False

    def detect_blocks(self, dx: int, dy: int) -> bool:
        for block in blocks:
            if self.detect_mob(dx, dy, block):
                return True
        return False

    def detect_enemies(self) -> bool:
        for enemy in enemies:
            if self.detect_mob(0, 0, enemy):
                return True
        return False

    def update(self) -> None:
        # Set direction
        self.dx = 0
        self.dy = min(self.dy + 1, 3)
        if is_left():
            self.dx = -1
            self.is_right = False
        elif is_right():
            self.dx = 1
            self.is_right = True
        if self.is_on_floor:
            if is_up() and get_wall_id(
                    self.x + TILE_PX // 2, self.y + TILE_PX // 2) == -1:
                self.z = 1 - self.z
                return
            if is_decided():
                self.dy = -5

        # Adjust position
        for block in blocks:
            if self.detect_mob(0, 0, block):
                if block.dx > 0:
                    self.x = block.x + block.__class__.right - self.__class__.left + 1
                elif block.dx < 0:
                    self.x = block.x + block.__class__.left - self.__class__.right - 1
                if block.dy > 0:
                    self.y = block.y + block.__class__.bottom - self.__class__.top + 1
                elif block.dy < 0:
                    self.y = block.y + block.__class__.top - self.__class__.bottom - 1
            if block.dx != 0 and self.detect_mob(block.dx, 1, block):
                self.dx += block.dx

        # Death
        if (self.detect_collision(0, 0)
                or self.detect_blocks(0, 0)):
            self.is_dead = True
            return

        # Move x direction
        abs_dx = abs(self.dx)
        sign_dx = 1 if self.dx > 0 else -1
        for _ in range(abs_dx):
            if (self.detect_collision(sign_dx, 0)
                    or self.detect_blocks(sign_dx, 0)):
                break
            self.x += sign_dx

        # Move y direction
        self.is_on_floor = False
        abs_dy = abs(self.dy)
        sign_dy = 1 if self.dy > 0 else -1
        for _ in range(abs_dy):
            if self.detect_collision(0, sign_dy):
                self.is_on_floor = self.dy > 0
                break
            for block in blocks:
                if self.detect_mob(0, sign_dy, block):
                    if self.dy > 0:
                        self.is_on_floor = True
                    break
            else:
                self.y += sign_dy
                continue
            break

        # Is hit enemies
        if self.detect_enemies():
            self.is_dead = True

    def draw(self) -> None:
        u = 0
        v = 4 * TILE_PX
        w = TILE_PX if self.is_right else -TILE_PX
        pyxel.blt(
            self.x, self.y, 0, u, v, w, TILE_PX, TRANSPARENT_COLOR)

class Block_line(Mob):
    def __init__(self, x_tile: int, y_tile: int, dx: int, dy: int) -> None:
        super().__init__(x_tile, y_tile)
        self.dx = dx
        self.dy = dy

    def update(self) -> None:
        if self.detect_collision(self.dx, self.dy):
            self.dx *= -1
            self.dy *= -1
        super().update()

class Block_cw(Mob):
    def __init__(self, x_tile: int, y_tile: int, dx: int, dy: int) -> None:
        super().__init__(x_tile, y_tile)
        self.dx = dx
        self.dy = dy

    def update(self) -> None:
        if self.detect_collision(self.dx, self.dy):
            if self.dx != 0:
                self.dy = self.dx
                self.dx = 0
            elif self.dy != 0:
                self.dx = -self.dy
                self.dy = 0
        super().update()

class Block_ccw(Mob):
    def __init__(self, x_tile: int, y_tile: int, dx: int, dy: int) -> None:
        super().__init__(x_tile, y_tile)
        self.dx = dx
        self.dy = dy

    def update(self) -> None:
        if self.detect_collision(self.dx, self.dy):
            if self.dx != 0:
                self.dy = -self.dx
                self.dx = 0
            elif self.dy != 0:
                self.dx = self.dy
                self.dy = 0
        super().update()

class Thorn_L(Mob):
    top    = 1
    bottom = 6
    left   = 0
    right  = 2
    u = 0
    v = 5 * TILE_PX

    def __init__(self, x_tile: int, y_tile: int) -> None:
        super().__init__(x_tile, y_tile)

class Thorn_R(Mob):
    top    = 1
    bottom = 6
    left   = 5
    right  = 7
    u = TILE_PX
    v = 5 * TILE_PX

    def __init__(self, x_tile: int, y_tile: int) -> None:
        super().__init__(x_tile, y_tile)

class Blade(Mob):
    top    = 2
    bottom = 5
    left   = 2
    right  = 5

    def __init__(self, x_tile: int, y_tile: int) -> None:
        super().__init__(x_tile, y_tile)

    def draw(self) -> None:
        u = (pyxel.frame_count // 2 % 4) * TILE_PX
        v = 7 * TILE_PX
        pyxel.blt(
            self.x, self.y, 0, u, v, TILE_PX, TILE_PX, TRANSPARENT_COLOR)

class Small_blade(Mob):
    top    = 5
    bottom = 6
    left   = 3
    right  = 4

    def __init__(self, x_tile: int, y_tile: int) -> None:
        super().__init__(x_tile, y_tile)

    def draw(self) -> None:
        u = (pyxel.frame_count // 2 % 4) * TILE_PX
        v = 6 * TILE_PX
        pyxel.blt(
            self.x, self.y, 0, u, v, TILE_PX, TILE_PX, TRANSPARENT_COLOR)

class Chest(Mob):
    top    = 2
    bottom = 7
    left   = 1
    right  = 6
    u = 2 * TILE_PX
    v = 5 * TILE_PX

    def __init__(self, x_tile: int, y_tile: int) -> None:
        super().__init__(x_tile, y_tile)
        pyxel.tilemap(player.z).pset(x_tile, y_tile, (0, 0))
        chests_pos.append((x_tile, y_tile, player.z))

def get_wall_id(x: int, y: int) -> int:
    tile = pyxel.tilemap(player.z).pget(x // TILE_PX, y // TILE_PX)
    if tile == (0, 3):
        return -1
    if tile == (4, 0):
        return 1
    if tile[1] >= 4:
        return 0
    if tile[0] == 0:
        return 0
    if tile[0] < 4:
        return 2
    return 0

def append_enemy(x_tile: int, y_tile: int) -> None:
    tile = pyxel.tilemap(player.z).pget(x_tile, y_tile)
    ut, vt = tile
    if ut < 4:
        return
    dx = 1 if ut == 4 else -1 if ut == 6 else 0
    dy = 1 if ut == 5 else -1 if ut == 7 else 0
    if vt == 1:
        blocks.append(Block_line(x_tile, y_tile, dx, dy))
    elif vt == 2:
        blocks.append(Block_cw(x_tile, y_tile, dx, dy))
    elif vt == 3:
        blocks.append(Block_ccw(x_tile, y_tile, dx, dy))
    elif tile == (4, 4):
        enemies.append(Thorn_L(x_tile, y_tile))
    elif tile == (4, 5):
        enemies.append(Thorn_R(x_tile, y_tile))
    elif tile == (4, 6):
        enemies.append(Small_blade(x_tile, y_tile))
    elif tile == (4, 7):
        enemies.append(Blade(x_tile, y_tile))
    elif tile == (5, 0):
        chests.append(Chest(x_tile, y_tile))

def draw_text(x: int, y: int, text: str) -> None:
    pyxel.text(x + 1, y + 2, text, TEXT_COLOR_1)
    pyxel.text(x,     y + 2, text, TEXT_COLOR_2)

class App:
    def __init__(self) -> None:
        pyxel.init(WIDTH_PX, HEIGHT_PX, title=GAME_TITLE)
        pyxel.load(PYXRES_NAME)
        self.reset()
        pyxel.image(0).rect(
            4 * TILE_PX, 0, 4 * TILE_PX, 8 * TILE_PX, TRANSPARENT_COLOR)
        pyxel.run(self.update, self.draw)

    def reset(self) -> None:
        self.respawn_x = INIT_X_TILE * TILE_PX
        self.respawn_y = INIT_Y_TILE * TILE_PX
        self.respawn_z = INIT_Z
        self.room = (
            INIT_X_TILE // WIDTH_TILE, INIT_Y_TILE // HEIGHT_TILE, INIT_Z)
        self.scroll_x = self.room[0] * WIDTH_PX
        self.scroll_y = self.room[1] * HEIGHT_PX
        self.scroll_dx = 0
        self.scroll_dy = 0
        self.time_h = 0
        self.time_m = 0
        self.time_s = 0
        self.chests_count = 0
        self.init_time = pyxel.frame_count
        self.death_time = -30
        self.is_ending = False
        global player, chests_pos
        player = Player(INIT_X_TILE, INIT_Y_TILE, INIT_Z)
        for pos in chests_pos:
            pyxel.tilemap(pos[2]).pset(pos[0], pos[1], (5, 0))
        chests_pos = []

    def update(self) -> None:
        if self.scroll_dx != 0 or self.scroll_dy != 0:
            self.scroll_x += self.scroll_dx
            self.scroll_y += self.scroll_dy
            if self.scroll_x % WIDTH_PX == 0:
                self.scroll_dx = 0
            if self.scroll_y % HEIGHT_PX == 0:
                self.scroll_dy = 0
            return
        self.update_game()

    def update_game(self) -> None:
        # Quit
        if pyxel.btn(pyxel.KEY_Q):
            pyxel.quit()

        # Time
        if pyxel.frame_count - self.death_time < 30:
            return
        if pyxel.frame_count - self.death_time == 30:
            pyxel.pal()
            player.respawn(self.respawn_x, self.respawn_y, self.respawn_z)
            self.update_room()

        # Move characters
        for block in blocks:
            block.update()
        player.update()
        if player.is_dead:
            pyxel.pal(6, 14)
            pyxel.pal(12, 8)
            pyxel.pal(5, 4)
            pyxel.play(1, 0)
            self.death_time = pyxel.frame_count
            return
        if player.dy == -5:
            pyxel.play(1, 1)

        # Chests
        i = 0
        while i < len(chests):
            item = chests[i]
            if player.detect_mob(0, 0, item):
                self.chests_count += 1
                chests.pop(i)
            else:
                i += 1

        # Scroll
        if self.is_ending:
            if is_down():
                self.reset()
        else:
            if self.room == END_ROOM:
                t = (pyxel.frame_count - self.init_time) // 30
                self.time_h = t // 3600
                self.time_m = (t // 60) % 60
                self.time_s = t % 60
                self.is_ending = True
            self.update_scroll()

    def update_scroll(self) -> None:
        old_room = self.room
        room_x, room_y, _ = old_room
        if player.x < room_x * WIDTH_PX - TILE_HALF:
            self.scroll_dx = -TILE_HALF
            room_x -= 1
        elif player.x > (room_x + 1) * WIDTH_PX - TILE_HALF:
            self.scroll_dx = TILE_HALF
            room_x += 1
        if player.y < room_y * HEIGHT_PX - TILE_HALF and player.is_on_floor:
            self.scroll_dy = -TILE_HALF
            room_y -= 1
        elif player.y > (room_y + 1) * HEIGHT_PX - TILE_HALF:
            self.scroll_dy = TILE_HALF
            room_y += 1
        self.room = (room_x, room_y, player.z)
        if self.room != old_room:
            pyxel.play(1, 0)
            self.update_room()

    def update_room(self) -> None:
        self.respawn_x = player.x
        self.respawn_y = player.y
        self.respawn_z = player.z
        global blocks, enemies
        blocks = []
        enemies = []
        yt_min = HEIGHT_TILE * self.room[1]
        yt_max = yt_min + HEIGHT_TILE
        for yt in range(yt_min, yt_max):
            xt_min = WIDTH_TILE * self.room[0]
            xt_max = xt_min + WIDTH_TILE
            for xt in range(xt_min, xt_max):
                append_enemy(xt, yt)

    def draw(self) -> None:
        # Draw background
        pyxel.cls(TRANSPARENT_COLOR)
        pyxel.camera(self.scroll_x, self.scroll_y)
        if self.room[0] > 12 and self.room[2] == 0:
            pyxel.bltm(
                self.scroll_x, self.scroll_y,
                player.z, (pyxel.frame_count // 4) % WIDTH_PX, 0,
                WIDTH_PX, HEIGHT_PX)

        # Draw level
        pyxel.bltm(
            self.scroll_x, self.scroll_y,
            player.z, self.scroll_x, self.scroll_y,
            WIDTH_PX, HEIGHT_PX, TRANSPARENT_COLOR)

        # Draw characters
        for item in chests:
            item.draw()
        player.draw()
        for block in blocks:
            block.draw()
        for enemy in enemies:
            enemy.draw()

        # Draw item counter
        pyxel.camera()
        for i in range(self.chests_count):
            pyxel.blt(
                i * TILE_PX, 0, 0, 2 * TILE_PX, 5 * TILE_PX,
                TILE_PX, TILE_PX, TRANSPARENT_COLOR)

        # Draw ending message
        if self.is_ending:
            draw_text(8, 16, "THANK YOU FOR YOUR PLAYING!")
            draw_text(
                16, 32,
                f"Time: {self.time_h}:{self.time_m:02}:{self.time_s:02}")
            draw_text(16, 48, f"Treasure chests: {self.chests_count}/3")
            draw_text(4, 96, "Put S key to restart the game!")

App()
