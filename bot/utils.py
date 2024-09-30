import requests
from PIL import Image
from io import BytesIO
from config import API_URL
import logging

logger = logging.getLogger(__name__)

def convert_to_square_webp(image_bytes):
    image = Image.open(BytesIO(image_bytes))
    
    # Определяем размер для квадратного изображения
    size = max(image.size)
    
    # Создаем новое квадратное изображение с белым фоном
    square_image = Image.new('RGB', (size, size), (255, 255, 255))
    
    # Вставляем исходное изображение в центр
    position = ((size - image.size[0]) // 2, (size - image.size[1]) // 2)
    square_image.paste(image, position)
    
    # Конвертируем в WebP
    webp_buffer = BytesIO()
    square_image.save(webp_buffer, format="WebP")
    webp_buffer.seek(0)
    
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