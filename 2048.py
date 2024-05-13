import os
import random
import tempfile
from PIL import Image, ImageDraw, ImageFont
import keyboard
import platform
import time

if platform.system() == "Windows":
    import winreg as reg
    import ctypes
else:
    import subprocess

BACKGROUND_PATH = os.path.join(tempfile.gettempdir(), "2048WE.png")

TILE_COLORS = {
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
    'higher': (60, 58, 50)
}

hack_mode_enabled = False

def tile_color(value):
    return TILE_COLORS.get(value, TILE_COLORS['higher'] if value > 2048 else (205, 193, 180))

def find_font():
    if platform.system() == "Windows":
        return "arial.ttf"
    else:
        preferred_fonts = ["DejaVu Sans Bold", "FreeSans Bold", "Arial"]
        for font in preferred_fonts:
            font_path = subprocess.getoutput(f"fc-match -f '%{{file}}' '{font}'")
            if font_path.endswith('.ttf') or font_path.endswith('.otf'):
                print(f"Using font: {font_path}")
                return font_path
        fallback_font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        print(f"No preferred font found, using fallback font: {fallback_font}")
        return fallback_font

FONT_PATH = find_font()

def set_wallpaper(img):
    img.save(BACKGROUND_PATH)
    if platform.system() == "Windows":
        set_wallpaper_windows(BACKGROUND_PATH)
    else:
        set_wallpaper_linux(BACKGROUND_PATH)

def save_original_wallpaper():
    global ORIGINAL_BACKGROUND_PATH, ORIGINAL_STYLE, ORIGINAL_TILE
    if platform.system() == "Windows":
        ORIGINAL_BACKGROUND_PATH = get_wallpaper_windows()
        ORIGINAL_STYLE, ORIGINAL_TILE = get_wallpaper_style_windows()
    else:
        ORIGINAL_BACKGROUND_PATH = get_wallpaper_linux()

def restore_original_wallpaper():
    if platform.system() == "Windows":
        set_wallpaper_windows(ORIGINAL_BACKGROUND_PATH)
        set_wallpaper_style_windows(ORIGINAL_STYLE, ORIGINAL_TILE)
    else:
        set_wallpaper_linux(ORIGINAL_BACKGROUND_PATH)

def get_wallpaper_windows():
    buffer = ctypes.create_unicode_buffer(256)
    if ctypes.windll.user32.SystemParametersInfoW(0x0073, 256, buffer, 0):
        return buffer.value
    raise RuntimeError("Failed to get wallpaper")

def get_wallpaper_linux():
    command = ["gsettings", "get", "org.gnome.desktop.background", "picture-uri"]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip().replace("'", "").replace("file://", "")
    raise RuntimeError("Failed to get wallpaper")

def set_wallpaper_windows(img_path):
    ctypes.windll.user32.SystemParametersInfoW(20, 0, img_path, 3)

def set_wallpaper_linux(img_path): # not tested
    desktop_env = os.getenv('XDG_CURRENT_DESKTOP', '').upper() or subprocess.getoutput('echo $XDG_CURRENT_DESKTOP').strip().upper()
    desktop_env = desktop_env.split()
    
    commands = {
        'GNOME': ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"file://{img_path}"],
        'KDE': [
            "qdbus", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript",
            f'desktops()[0].wallpaperPlugin = "org.kde.image"; desktops()[0].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"]; desktops()[0].writeConfig("Image", "file://{img_path}")'
        ],
        'XFCE': ["xfconf-query", "--channel", "xfce4-desktop", "--property", "/backdrop/screen0/monitor0/workspace0/last-image", "--set", img_path],
        'FEH': ["feh", "--bg-scale", img_path]
    }
    
    command = commands.get(desktop_env[0] if desktop_env else "FEH", ["feh", "--bg-scale", img_path])

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to set wallpaper for {desktop_env}: {e}")
        raise RuntimeError("Failed to set wallpaper")

def get_wallpaper_style_windows():
    with reg.OpenKey(reg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, reg.KEY_READ) as key:
        style = reg.QueryValueEx(key, "WallpaperStyle")[0]
        tile = reg.QueryValueEx(key, "TileWallpaper")[0]
        return style, tile

def set_wallpaper_style_windows(style='0', tile='0'):
    with reg.OpenKey(reg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, reg.KEY_WRITE) as key:
        reg.SetValueEx(key, "WallpaperStyle", 0, reg.REG_SZ, style)
        reg.SetValueEx(key, "TileWallpaper", 0, reg.REG_SZ, tile)

def new_board(size=4):
    return [[0] * size for _ in range(size)]

def add_new_tile(board):
    empty_tiles = [(x, y) for x in range(len(board)) for y in range(len(board[x])) if board[x][y] == 0]
    if empty_tiles:
        x, y = random.choice(empty_tiles)
        if hack_mode_enabled:
            board[x][y] = random.choice([8, 16])
        else:
            board[x][y] = random.choices([2, 4], weights=[0.9, 0.1], k=1)[0]
    return board

def has_possible_combinations(board):
    for i in range(len(board)):
        for j in range(len(board[i])):
            if board[i][j] == 0 or (j < len(board[i]) - 1 and board[i][j] == board[i][j + 1]) or (i < len(board) - 1 and board[i][j] == board[i + 1][j]):
                return True
    return False

def move_row_left(row):
    result = [tile for tile in row if tile]
    i = 0
    while i < len(result) - 1:
        if result[i] == result[i + 1]:
            result[i] *= 2
            result.pop(i + 1)
            result.append(0)
        i += 1
    return result + [0] * (len(row) - len(result))

def move_board(board, direction):
    if direction in ['up', 'down']:
        board = [list(row) for row in zip(*board)]
    if direction in ['right', 'down']:
        board = [row[::-1] for row in board]
    board = [move_row_left(row) for row in board]
    if direction in ['right', 'down']:
        board = [row[::-1] for row in board]
    if direction in ['up', 'down']:
        board = [list(row) for row in zip(*board)]
    return board

def draw_game_over(img, game_over):
    if game_over:
        draw = ImageDraw.Draw(img)
        text = "Game Over"
        font = ImageFont.truetype(FONT_PATH, 60)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        w, h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        draw.text(
            ((img.width - w) // 2, (img.height - h) // 2),
            text,
            font=font,
            fill=(0, 0, 0, 128),
            stroke_width=2,
            stroke_fill=(255, 255, 255, 128)
        )

def check_for_2048(board):
    for row in board:
        if 2048 in row:
            return True
    return False

def display_2048_message(img):
    draw = ImageDraw.Draw(img)
    text = "2048!"
    font = ImageFont.truetype(FONT_PATH, 100)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    w, h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    draw.text(
        ((img.width - w) // 2, (img.height - h) // 2),
        text,
        font=font,
        fill=(255, 215, 0)
    )
    set_wallpaper(img)
    time.sleep(3)

def render_board(board, size=4, tile_size=100, background_color=(187, 173, 160), game_over=False):
    img_size = size * tile_size
    img = Image.new('RGBA', (img_size, img_size), background_color)
    draw = ImageDraw.Draw(img)

    for x in range(size):
        for y in range(size):
            value = board[y][x]
            if value:
                draw.rectangle(
                    [x * tile_size, y * tile_size, (x + 1) * tile_size, (y + 1) * tile_size],
                    fill=tile_color(value),
                    outline=(197, 173, 160),
                    width=2
                )
                text = str(value)
                font = ImageFont.truetype(FONT_PATH, 40)
                text_bbox = draw.textbbox((0, 0), text, font=font)
                w, h = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
                draw.text(
                    (x * tile_size + (tile_size - w) // 2, y * tile_size + (tile_size - h) // 2),
                    text,
                    font=font,
                    fill='black' if value < 8 else 'white'
                )
    draw_game_over(img, game_over)
    return img

def handle_input(board):
    if keyboard.is_pressed('m'):
        return 'hack'
    if keyboard.is_pressed('r'):
        return 'restart'
    if keyboard.is_pressed('esc'):
        return 'exit'
    keys_to_directions = {
        'left': 'left', 'a': 'left',
        'right': 'right', 'd': 'right',
        'up': 'up', 'w': 'up',
        'down': 'down', 's': 'down'
    }
    for key, direction in keys_to_directions.items():
        if keyboard.is_pressed(key):
            return move_board(board, direction)
    return None

def game_loop():
    global hack_mode_enabled

    save_original_wallpaper()

    if platform.system() == "Windows":
        set_wallpaper_style_windows('0', '0') # I recommend stretch or center (6 or 0) ~ the first number
        # 10 for fit, 6 for stretch, 2 for tile, 0 for center, 22 for span (+Win8)

    board = new_board()
    board = add_new_tile(board)
    board = add_new_tile(board)
    print("Game started")
    previous_board = None
    reached_2048 = False

    try:
        while True:
            if board != previous_board:
                img = render_board(board)
                set_wallpaper(img)
                previous_board = board.copy()

            if check_for_2048(board) and not reached_2048:
                display_2048_message(img)
                reached_2048 = True

            new_board_state = None
            while not new_board_state:
                time.sleep(0.05)
                new_board_state = handle_input(board)
                if new_board_state == 'restart':
                    print("Restarting game...")
                    board = new_board()
                    board = add_new_tile(board)
                    board = add_new_tile(board)
                    reached_2048 = False
                elif new_board_state == 'exit':
                    print("Exiting game...")
                    restore_original_wallpaper()
                    return
                elif new_board_state == 'hack':
                    time.sleep(1)
                    hack_mode_enabled = not hack_mode_enabled
                    print("Hack mode enabled" if hack_mode_enabled else "Hack mode disabled")
                elif new_board_state and new_board_state != board:
                    board = add_new_tile(new_board_state)

            if not has_possible_combinations(board):
                img = render_board(board, game_over=True)
                set_wallpaper(img)
                print("Game over... Restarting in 5 seconds.")
                time.sleep(5)
                board = new_board()
                board = add_new_tile(board)
                board = add_new_tile(board)

    except KeyboardInterrupt:
        print("Game closed")
        restore_original_wallpaper()

if __name__ == "__main__":
    game_loop()
