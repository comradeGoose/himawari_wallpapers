import os
import ctypes
import requests
from PIL import Image


BASE_URL = "https://himawari8-dl.nict.go.jp/himawari8/img/D531106"  # Базовый URL для Himawari-8
GRANULARITY = 4  # Детализация: 1d, 2d, 4d, 8d, 16d (чем выше степень, тем больше сегментов)
RESOLUTION = 550  # Размер сегмента: 550 px
TIMESTAMP = "2024/12/29/044000"  # Время в формате ГГГГ/ММ/ДД/ЧЧММСС

# Папка для загрузки сегментов
OUTPUT_DIR = "himawari_segments"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_segment(x, y):
    """Скачивает один сегмент изображения."""
    segment_url = f"{BASE_URL}/{GRANULARITY}d/{RESOLUTION}/{TIMESTAMP}_{x}_{y}.png"
    response = requests.get(segment_url)
    if response.status_code == 200:
        segment_path = os.path.join(OUTPUT_DIR, f"segment_{x}_{y}.png")
        with open(segment_path, "wb") as file:
            file.write(response.content)
        print(f"Сегмент ({x}, {y}) загружен.")
        return segment_path
    else:
        print(f"Ошибка загрузки сегмента ({x}, {y}): {response.status_code}")
        return None

# Скачивание всех сегментов
def download_all_segments(grid_size):
    """Скачивает все сегменты и возвращает их пути."""
    segment_paths = []
    for y in range(grid_size):
        for x in range(grid_size):
            path = download_segment(x, y)
            if path:
                segment_paths.append((path, x, y))
    return segment_paths

# Объединение сегментов в одно изображение
def combine_segments(segment_paths, grid_size):
    """Объединяет сегменты в одно изображение."""
    full_image = Image.new("RGB", (RESOLUTION * grid_size, RESOLUTION * grid_size))
    for path, x, y in segment_paths:
        segment = Image.open(path)
        full_image.paste(segment, (x * RESOLUTION, y * RESOLUTION))
    return full_image

def set_wallpaper():
    ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.abspath("himawari_full_image.png") , 0)
    print("himawari_full_image.png установлено как фоновое изображение рабочего стола.")

# Основной процесс
if __name__ == "__main__":
    print("Скачиваем сегменты...")
    segments = download_all_segments(GRANULARITY)
    if segments:
        print("Объединяем изображение...")
        full_image = combine_segments(segments, GRANULARITY)
        full_image.save(f"himawari_full_image.png")
        print("Полное изображение сохранено как himawari_full_image.png")
        set_wallpaper()
