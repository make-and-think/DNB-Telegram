import requests
from wand.image import Image
from io import BytesIO
from config import API_URL
import logging

logger = logging.getLogger(__name__)


def convert_to_square_webp(image_bytes):
    # Преобразуем image_bytes в байтовый объект
    image_bytes = bytes(image_bytes)
    
    with Image(blob=image_bytes) as image:
        # Определяем размер для квадратного изображения
        size = max(image.width, image.height)

        # Создаем новое квадратное изображение с белым фоном
        with Image(width=size, height=size, background='white') as square_image:
            # Вставляем исходное изображение в центр
            left = (size - image.width) // 2
            top = (size - image.height) // 2
            square_image.composite(image, left=left, top=top)

            # Конвертируем в WebP
            square_image.format = 'webp'
            webp_buffer = BytesIO(square_image.make_blob())

    return webp_buffer


def send_to_api(webp_buffer):
    files = {'image': ('image.webp', webp_buffer, 'image/webp')}
    try:
        response = requests.put(f"{API_URL}/wd_tagger/all", files=files, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending request to API: {e}")
        return None
