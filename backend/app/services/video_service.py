"""
Сервис для работы с видео-файлами: валидация, обработка, превью.
"""
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict
import json


def get_video_info(video_path: Path) -> Optional[Dict]:
    """
    Получает информацию о видео-файле используя ffprobe.
    
    Returns:
        Dict с полями: duration, width, height, bitrate, codec, format
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        
        data = json.loads(result.stdout)
        
        # Находим видео поток
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            return None
        
        format_info = data.get('format', {})
        
        return {
            'duration': float(format_info.get('duration', 0)),
            'width': int(video_stream.get('width', 0)),
            'height': int(video_stream.get('height', 0)),
            'bitrate': int(format_info.get('bit_rate', 0)),
            'codec': video_stream.get('codec_name'),
            'format': format_info.get('format_name'),
            'size': int(format_info.get('size', 0)),
            'fps': eval(video_stream.get('r_frame_rate', '0/1'))
        }
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error getting video info: {e}")
        return None


def validate_video_file(video_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Валидирует видео-файл: проверяет формат и целостность.
    
    Returns:
        (is_valid, error_message)
    """
    if not video_path.exists():
        return False, "File does not exist"
    
    info = get_video_info(video_path)
    if not info:
        return False, "Invalid video file or unable to read video information"
    
    if info.get('duration', 0) <= 0:
        return False, "Video has zero or negative duration"
    
    if info.get('width', 0) <= 0 or info.get('height', 0) <= 0:
        return False, "Invalid video dimensions"
    
    return True, None


def generate_video_thumbnail(
    video_path: Path,
    output_path: Path,
    time_offset: float = 1.0,
    width: int = 320,
    height: int = 240
) -> bool:
    """
    Генерирует превью (thumbnail) для видео.
    
    Args:
        video_path: Путь к видео-файлу
        output_path: Путь для сохранения превью
        time_offset: Время в секундах от начала видео для кадра
        width: Ширина превью
        height: Высота превью
    
    Returns:
        True если успешно
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-ss', str(time_offset),
            '-vframes', '1',
            '-vf', f'scale={width}:{height}',
            '-y',  # Перезаписать если существует
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0 and output_path.exists()
    
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Error generating video thumbnail: {e}")
        return False


def extract_video_frame(
    video_path: Path,
    output_path: Path,
    time_offset: float = 0.0
) -> bool:
    """
    Извлекает кадр из видео в указанное время.
    
    Args:
        video_path: Путь к видео-файлу
        output_path: Путь для сохранения кадра
        time_offset: Время в секундах от начала видео
    
    Returns:
        True если успешно
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-ss', str(time_offset),
            '-vframes', '1',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0 and output_path.exists()
    
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Error extracting video frame: {e}")
        return False


def is_video_file(file_path: Path) -> bool:
    """
    Проверяет, является ли файл видео.
    """
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}
    return file_path.suffix.lower() in video_extensions


def check_ffmpeg_available() -> bool:
    """
    Проверяет, доступен ли ffmpeg/ffprobe в системе.
    """
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        subprocess.run(['ffprobe', '-version'], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

