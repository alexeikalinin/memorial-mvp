"""
Сервис для работы с медиа-файлами: генерация миниатюр, валидация, обработка.
"""
import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import io
from app.config import settings
from app.models import MediaType


# Размеры миниатюр
THUMBNAIL_SIZES = {
    "small": (150, 150),
    "medium": (300, 300),
    "large": (800, 800),
}


def generate_thumbnail(
    image_path: Path,
    output_path: Path,
    size: Tuple[int, int] = THUMBNAIL_SIZES["medium"],
    quality: int = 85
) -> bool:
    """
    Генерирует миниатюру изображения.
    
    Args:
        image_path: Путь к исходному изображению
        output_path: Путь для сохранения миниатюры
        size: Размер миниатюры (width, height)
        quality: Качество JPEG (1-100)
    
    Returns:
        True если успешно, False в противном случае
    """
    try:
        with Image.open(image_path) as img:
            # Конвертация в RGB если необходимо (для PNG с прозрачностью)
            if img.mode in ("RGBA", "LA", "P"):
                # Создаем белый фон
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = rgb_img
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            # Создание миниатюры с сохранением пропорций
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Сохранение
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "JPEG", quality=quality, optimize=True)
            return True
    
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return False


def generate_all_thumbnails(image_path: Path, base_output_dir: Path) -> dict:
    """
    Генерирует все размеры миниатюр для изображения.
    
    Returns:
        Dict с путями к миниатюрам: {"small": path, "medium": path, "large": path}
    """
    thumbnails = {}
    image_stem = image_path.stem
    
    for size_name, size in THUMBNAIL_SIZES.items():
        thumbnail_path = base_output_dir / f"{image_stem}_{size_name}.jpg"
        if generate_thumbnail(image_path, thumbnail_path, size):
            thumbnails[size_name] = str(thumbnail_path)
    
    return thumbnails


def validate_image_file(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Валидирует изображение: проверяет формат и целостность.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        with Image.open(file_path) as img:
            img.verify()  # Проверка целостности
        return True, None
    except Exception as e:
        return False, str(e)


def get_image_dimensions(image_path: Path) -> Optional[Tuple[int, int]]:
    """
    Получает размеры изображения (width, height).
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception:
        return None


def optimize_image(
    image_path: Path,
    output_path: Optional[Path] = None,
    max_size: Optional[Tuple[int, int]] = None,
    quality: int = 85
) -> bool:
    """
    Оптимизирует изображение: сжатие и изменение размера при необходимости.
    
    Args:
        image_path: Путь к исходному изображению
        output_path: Путь для сохранения (если None, перезаписывает исходный)
        max_size: Максимальный размер (width, height)
        quality: Качество JPEG (1-100)
    
    Returns:
        True если успешно
    """
    try:
        with Image.open(image_path) as img:
            # Конвертация в RGB
            if img.mode in ("RGBA", "LA", "P"):
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = rgb_img
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            # Изменение размера если необходимо
            if max_size and (img.width > max_size[0] or img.height > max_size[1]):
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Сохранение
            output = output_path or image_path
            output.parent.mkdir(parents=True, exist_ok=True)
            img.save(output, "JPEG", quality=quality, optimize=True)
            return True
    
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return False


def get_file_size_mb(file_path: Path) -> float:
    """Получает размер файла в мегабайтах."""
    return file_path.stat().st_size / (1024 * 1024)


def is_image_file(file_path: Path) -> bool:
    """Проверяет, является ли файл изображением."""
    try:
        with Image.open(file_path) as img:
            return True
    except Exception:
        return False

