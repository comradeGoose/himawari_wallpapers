import os, shutil
import ctypes
import requests
import socket
import struct
from datetime import datetime, timezone, timedelta
from PIL import Image

BASE_URL = "https://himawari8-dl.nict.go.jp/himawari8/img/D531106"  # Базовый URL для Himawari-8
GRANULARITY = 4  # Детализация: 1d, 2d, 4d, 8d, 16d (чем выше степень, тем больше сегментов n*n 16*16 = 60.5 Mb)
RESOLUTION = 550  # Размер сегмента: 550 px
TIMESTAMP = "2024/12/30/060000"  # Время в формате ГГГГ/ММ/ДД/ЧЧММСС

REF_TIME_1970 = 2208988800  # Смещение для преобразования NTP-времени в UNIX-время

# Папка для загрузки сегментов
OUTPUT_DIR = "image/himawari_segments"
# os.makedirs(OUTPUT_DIR, exist_ok=True)

def request_time_from_ntp(addr='0.de.pool.ntp.org'):
    """
    Получение текущего времени UTC с NTP-сервера.

    :param addr: адрес NTP-сервера
    :return: строковое представление времени UTC и UNIX-время
    """
    
    print("Получение текущего времени UTC с NTP-сервера.")
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Формируем NTP-запрос (48 байт)
        data = b'\x1b' + 47 * b'\0'
        # Отправляем запрос на NTP-сервер
        client.sendto(data, (addr, 123))
        # Получаем ответ от NTP-сервера
        data = client.recvfrom(1024)[0]
        if data:
            # Извлекаем время из ответа
            t = struct.unpack('!12I', data)[10]
            t -= REF_TIME_1970  # Переводим в UNIX-время
            # Преобразуем в формат UTC
            utc_time = datetime.fromtimestamp(t, tz=timezone.utc)
            # Добавляем 20 минут
            adjusted_time = utc_time - timedelta(minutes=20)
            # Округляем минуты до десятков
            rounded_minutes = (adjusted_time.minute // 10) * 10
            final_time = adjusted_time.replace(minute=rounded_minutes, second=0)
            return f"Время UTC (GMT-0):", final_time.strftime('%Y/%m/%d/%H%M%S')
    except Exception as e:
        return f"Ошибка: {e}", None
    finally:
        client.close()

def download_segment(x, y, timestamp):
    """
    Скачивает один сегмент изображения.

    :param x: 
    :param y: 
    :return: путь сегмента
    """
    
    segment_url = f"{BASE_URL}/{GRANULARITY}d/{550}/{timestamp}_{x}_{y}.png"
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
    """
    Скачивает все сегменты и возвращает их пути.
    
    :param grid_size: 
    :return: 
    """
    
    timestamp = request_time_from_ntp()
    print(timestamp)
    segment_paths = []
    for y in range(grid_size):
        for x in range(grid_size):
            path = download_segment(x, y, timestamp[1])
            if path:
                segment_paths.append((path, x, y))
    return segment_paths

# Объединение сегментов в одно изображение
def combine_segments(segment_paths, grid_size):
    """
    Объединяет сегменты в одно изображение.
    
    :param segment_paths: 
    :param grid_size: 
    :return: 
    """
    
    print("Объединяем изображение...")
    full_image = Image.new("RGB", (RESOLUTION * grid_size, RESOLUTION * grid_size))
    for path, x, y in segment_paths:
        segment = Image.open(path)
        full_image.paste(segment, (x * RESOLUTION, y * RESOLUTION))
    return full_image

def delete_segments():
    """"""
    print("Удаляем сегменты...")
    for filename in os.listdir(OUTPUT_DIR):
        file_path = os.path.join(OUTPUT_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def set_wallpaper():
    """Устанавливает фоновое изображение рабочего стола."""

    ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.abspath("image/himawari_full_image.png") , 0)
    print("himawari_full_image.png установлено как фоновое изображение рабочего стола.")

# Основной процесс
if __name__ == "__main__":

    # while 1:

    print("Скачиваем сегменты...")
    segments = download_all_segments(GRANULARITY)
    if segments:
        full_image = combine_segments(segments, GRANULARITY)
        full_image.save(f"image/himawari_full_image.png")
        print("Полное изображение сохранено как himawari_full_image.png")
        delete_segments()
        set_wallpaper()
        
        # time.sleep(600)
    
