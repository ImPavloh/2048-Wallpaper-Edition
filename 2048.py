import os
import random
import tempfile
from PIL import Image, ImageDraw, ImageFont
import keyboard
import ctypes
import time

BACKGROUND_PATH = os.path.join(tempfile.gettempdir(), "2048.png")

def new_board(size=4):
    return [[0] * size for _ in range(size)]

def add_new_tile(board, size=4):
    empty_tiles = [(x, y) for x in range(size) for y in range(size) if board[x][y] == 0]
    if empty_tiles:
        x, y = random.choice(empty_tiles)
        board[x][y] = random.choices([2, 4], weights=[0.75, 0.25])[0]
    elif not has_possible_combinations(board):
        img = render_board(board, game_over=True)
        set_wallpaper(img)
        print("Game Over... Restarting game...")
        time.sleep(5)
        main()

def has_possible_combinations(board):
    for row in board:
        if 0 in row:
            return True
    for i in range(len(board)):
        for j in range(len(board[0]) - 1):
            if board[i][j] == board[i][j + 1] or board[j][i] == board[j + 1][i]:
                return True

    return False

def move_row_left(row):
    non_zeros = [x for x in row if x != 0]
    new_row = []
    skip = False

    for i in range(len(non_zeros)):
        if skip:
            skip = False
            continue

        if i < len(non_zeros) - 1 and non_zeros[i] == non_zeros[i + 1]:
            new_row.append(2 * non_zeros[i])
            skip = True
        else:
            new_row.append(non_zeros[i])

    return new_row + [0] * (len(row) - len(new_row))

def move_board(board, direction):
    size = len(board)
    if direction == 'left':
        board = [move_row_left(row) for row in board]
    elif direction == 'right':
        board = [move_row_left(row[::-1])[::-1] for row in board]
    elif direction == 'up':
        board = [list(row) for row in zip(*[move_row_left(row) for row in zip(*board)])]
    elif direction == 'down':
        board = [list(row) for row in zip(*[move_row_left(row[::-1])[::-1] for row in zip(*board)])]
    return board

def tile_color(value):
    colors = {
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
    }
    return colors.get(value, (205, 193, 180))

def draw_game_over(img, game_over=False):
    if game_over:
        draw = ImageDraw.Draw(img)
        text = "Game over"
        font = ImageFont.truetype("arial.ttf", 60)
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
                font = ImageFont.truetype("arial.ttf", 40)
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

def set_wallpaper(img):
    img.save(BACKGROUND_PATH)
    ctypes.windll.user32.SystemParametersInfoW(20, 0, BACKGROUND_PATH, 3)

def main():
    board = new_board()
    add_new_tile(board)
    add_new_tile(board)

    while True:
        img = render_board(board)
        set_wallpaper(img)

        if keyboard.is_pressed('left'):
            board = move_board(board, 'left')
            add_new_tile(board)
        elif keyboard.is_pressed('right'):
            board = move_board(board, 'right')
            add_new_tile(board)
        elif keyboard.is_pressed('up'):
            board = move_board(board, 'up')
            add_new_tile(board)
        elif keyboard.is_pressed('down'):
            board = move_board(board, 'down')
            add_new_tile(board)
        elif keyboard.is_pressed('R'):
            main()

if __name__ == "__main__":
    print("Game started")
    main()
