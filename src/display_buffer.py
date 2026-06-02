"""
Headless renderer for the web frontend.

Renders a game frame to a 2D JSON-serialisable buffer instead of a terminal.
Each cell is {"char": str, "color": str} where color is a CSS hex string.
"""

from gameObjects.obstacle import JellyfishObstacle, PufferfishObstacle

BUFFER_COLS = 100
GAME_AREA_HEIGHT = 30   # visible rows (y = 0 .. GAME_AREA_HEIGHT-1)
HEADER_ROWS = 4         # rows 0-3: blank + dash + score/title + dash

BG = "#001133"
PLAYER_COLOR = "#FFFF00"
PLAYER_DEAD_COLOR = "#FF4444"
CRAB_COLOR = "#FF4444"
TENTACLE_COLOR = "#00CC00"
JELLYFISH_COLOR = "#FF69B4"
PUFFERFISH_COLOR = "#FFFF00"
COIN_COLOR = "#FFD700"
BUBBLE_COLOR = "#00FFFF"
AMBIENT_COLOR = "#00FFFF"
JF_BUBBLE_COLOR = "#006666"
HEADER_COLOR = "#CCCCCC"

_SWAP_MAP = str.maketrans(r"/\()<>[]{}", r"\/)(><][}{")


def render_frame(
    player,
    obstacles,
    score: int,
    high_score: int,
    bubbles=None,
    ambient_bubbles=None,
    crabs=None,
    crab_frames=None,
    crab_y: int = 0,
    jellyfishes=None,
    jf_sprites=None,
    jf_bubbles=None,
    tentacle_frame: int = 0,
    coins=None,
) -> dict:
    """Return {"buffer": 2D list, "score": int, "high_score": int}."""
    cols = BUFFER_COLS
    total_rows = HEADER_ROWS + GAME_AREA_HEIGHT  # 34

    buffer = [[{"char": " ", "color": BG} for _ in range(cols)] for _ in range(total_rows)]

    def set_cell(row, col, char, color):
        if 0 <= row < total_rows and 0 <= col < cols and char != " ":
            buffer[row][col] = {"char": char, "color": color}

    # --- Header ---
    # Row 0: blank (already BG)
    # Row 1: dashes
    for c in range(cols):
        buffer[1][c] = {"char": "-", "color": HEADER_COLOR}
    # Row 2: score / title / high score
    score_str = f"Score: {str(score).rjust(3, '0')}"
    title_str = "Flappy Fisherman"
    hs_str = f"High Score: {str(high_score).rjust(3, '0')}"
    left_pad = max(1, cols // 2 - len(score_str) - len(title_str) // 2)
    right_pad = max(1, cols - len(score_str) - left_pad - len(title_str) - len(hs_str))
    row2_str = score_str + " " * left_pad + title_str + " " * right_pad + hs_str
    for c, ch in enumerate(row2_str[:cols]):
        buffer[2][c] = {"char": ch, "color": HEADER_COLOR}
    # Row 3: dashes
    for c in range(cols):
        buffer[3][c] = {"char": "-", "color": HEADER_COLOR}

    # --- Lookup maps (same logic as display.py) ---
    bubble_set = {(round(b[0]), round(b[1])) for b in bubbles} if bubbles else set()

    crab_map: dict = {}
    if crabs and crab_frames:
        for c in crabs:
            cx = round(c[0])
            frame = crab_frames[int(c[1])]
            for row_i, row in enumerate(frame):
                ry = crab_y + row_i
                for col_i, ch in enumerate(row):
                    if ch != " ":
                        crab_map[(cx + col_i, ry)] = ch

    jf_map: dict = {}
    if jellyfishes and jf_sprites:
        for jf in jellyfishes:
            cx, cy = round(jf[0]), round(jf[1])
            sprite = jf_sprites[int(jf[2])]
            for row_i, row in enumerate(sprite):
                for col_i, ch in enumerate(row):
                    if ch != " ":
                        jf_map[(cx + col_i, cy + row_i)] = ch

    jf_bubble_map: dict = {}
    if jf_bubbles:
        for b in jf_bubbles:
            jf_bubble_map[(round(b[0]), round(b[1]))] = b[4]

    ambient_map: dict = {}
    if ambient_bubbles:
        for b in ambient_bubbles:
            ambient_map[(round(b[0]), round(b[1]))] = b[3]

    coin_map: dict = {}
    if coins:
        for coin in coins:
            cx, cy = coin.position
            for row_i, row in enumerate(coin.sprite.display):
                for col_i, ch in enumerate(row):
                    if ch != " ":
                        coin_map[(cx + col_i, cy + row_i)] = ch

    px, py = round(player.position[0]), round(player.position[1])

    # --- Game area ---
    for y in range(GAME_AREA_HEIGHT):
        buf_row = y + HEADER_ROWS
        for x in range(cols):
            # Priority: player > crabs > obstacles > coins > fish bubbles > deco jf > jf bubbles > ambient
            if px <= x < px + player.width and py <= y < py + player.height:
                ch = player.sprite.display[y - py][x - px]
                color = PLAYER_DEAD_COLOR if player.is_dead else PLAYER_COLOR
                set_cell(buf_row, x, ch, color)
            elif (x, y) in crab_map:
                set_cell(buf_row, x, crab_map[(x, y)], CRAB_COLOR)
            else:
                hit_obs = None
                for obs in obstacles:
                    ox, oy = round(obs.position[0]), round(obs.position[1])
                    if ox <= x < ox + obs.width and oy <= y < oy + obs.height:
                        hit_obs = obs
                        break
                if hit_obs is not None:
                    obs = hit_obs
                    ox, oy = round(obs.position[0]), round(obs.position[1])
                    lx, ly = x - ox, y - oy
                    row_data = obs.sprite.display[ly]
                    if isinstance(obs, JellyfishObstacle):
                        ch = row_data[lx] if lx < len(row_data) else " "
                        set_cell(buf_row, x, ch, JELLYFISH_COLOR)
                    elif isinstance(obs, PufferfishObstacle):
                        ch = row_data[lx] if lx < len(row_data) else " "
                        set_cell(buf_row, x, ch, PUFFERFISH_COLOR)
                    else:
                        if tentacle_frame == 1:
                            row_str = "".join(row_data)
                            half = len(row_str) // 2
                            new_row = list(
                                row_str[:half][::-1].translate(_SWAP_MAP)
                                + row_str[half:][::-1].translate(_SWAP_MAP)
                            )
                            ch = new_row[lx] if lx < len(new_row) else " "
                        else:
                            ch = row_data[lx] if lx < len(row_data) else " "
                        set_cell(buf_row, x, ch, TENTACLE_COLOR)
                elif (x, y) in coin_map:
                    set_cell(buf_row, x, coin_map[(x, y)], COIN_COLOR)
                elif (x, y) in bubble_set:
                    set_cell(buf_row, x, "o", BUBBLE_COLOR)
                elif (x, y) in jf_map:
                    set_cell(buf_row, x, jf_map[(x, y)], JELLYFISH_COLOR)
                elif (x, y) in jf_bubble_map:
                    set_cell(buf_row, x, jf_bubble_map[(x, y)], JF_BUBBLE_COLOR)
                elif (x, y) in ambient_map:
                    set_cell(buf_row, x, ambient_map[(x, y)], AMBIENT_COLOR)

    return {"buffer": buffer, "score": score, "high_score": high_score}
