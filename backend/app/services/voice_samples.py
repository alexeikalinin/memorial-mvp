"""Prepare uploaded voice recordings; video is decoded locally, never sent to TTS."""
import asyncio
import json
from pathlib import Path
import uuid

MAX_SAMPLE_BYTES = 100 * 1024 * 1024
MAX_VIDEO_SECONDS = 600
VIDEO_SUFFIXES = {'.mp4', '.mov', '.m4v', '.webm'}
AUDIO_SUFFIXES = {'.mp3', '.wav', '.m4a', '.ogg', '.oga', '.opus', '.webm', '.flac', '.aac', '.mpeg', '.mpga'}


def supported_sample(upload):
    suffix = Path(upload.filename or '').suffix.lower()
    mime = (upload.content_type or '').lower()
    return (mime.startswith('audio/') or suffix in AUDIO_SUFFIXES
            or (suffix in VIDEO_SUFFIXES and mime in ('video/mp4', 'video/quicktime', 'video/webm', 'video/x-m4v', 'application/octet-stream', '')))


async def _run(*args):
    try:
        process = await asyncio.create_subprocess_exec(
            *args, stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise RuntimeError('Извлечение звука из видео временно недоступно: на сервере отсутствует FFmpeg.') from exc
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
    except BaseException:
        if process.returncode is None:
            process.kill()
        await process.communicate()
        raise
    if process.returncode:
        raise ValueError('Не удалось прочитать видео. Проверьте, что файл не повреждён и содержит аудиодорожку.')
    return stdout


async def extract_video_audio(source: Path, destination: Path):
    try:
        info = json.loads(await _run('ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-show_streams', '-show_format', '-of', 'json', str(source)))
        streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'audio']
        if not streams:
            raise ValueError('В видео нет аудиодорожки. Выберите видео, в котором слышен голос.')
        duration = info.get('format', {}).get('duration') or streams[0].get('duration')
        if duration is None or float(duration) <= 0:
            raise ValueError('Не удалось определить длительность видео. Выберите другой файл.')
        if float(duration) > MAX_VIDEO_SECONDS:
            raise ValueError('Видео для клонирования должно быть не длиннее 10 минут. Загрузите фрагмент с голосом нужного человека.')
        await _run('ffmpeg', '-nostdin', '-v', 'error', '-y', '-protocol_whitelist', 'file,pipe', '-i', str(source),
                   '-map', '0:a:0', '-vn', '-ac', '1', '-ar', '44100',
                   '-c:a', 'libmp3lame', '-b:a', '128k', str(destination))
        if not destination.exists() or not destination.stat().st_size:
            raise ValueError('Не удалось извлечь звук из видео.')
    except asyncio.TimeoutError as exc:
        raise ValueError('Обработка видео заняла слишком много времени. Выберите более короткий фрагмент.') from exc


async def prepare_voice_samples(uploads, directory: Path):
    """Return temporary audio paths. Caller owns cleanup after a successful return."""
    if not all(supported_sample(f) for f in uploads):
        raise ValueError('Выберите аудиозапись (MP3, WAV, M4A, OGG) или видео (MP4, MOV, M4V, WEBM).')
    directory.mkdir(parents=True, exist_ok=True)
    created = []
    results = []
    try:
        for upload in uploads:
            suffix = Path(upload.filename or '').suffix.lower() or '.mp3'
            source = directory / f'voice_{uuid.uuid4().hex}{suffix}'
            created.append(source)
            size = 0
            with source.open('wb') as output:
                while chunk := await upload.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_SAMPLE_BYTES:
                        raise ValueError('Размер одного образца не должен превышать 100 МБ.')
                    output.write(chunk)
            if not size:
                raise ValueError('Загруженный файл пуст.')
            is_video = suffix in {'.mp4', '.mov', '.m4v'} or (upload.content_type or '').startswith('video/')
            if is_video:
                audio = source.with_suffix('.mp3')
                created.append(audio)
                await extract_video_audio(source, audio)
                source.unlink()
                results.append(audio)
            else:
                results.append(source)
        return results
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
