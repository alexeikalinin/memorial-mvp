"""Bound provider requests without discarding any of the requested speech."""
import asyncio
from pathlib import Path
import tempfile


def speech_chunks(text, limit=3000):
    chunks = []
    while len(text) > limit:
        # Prefer paragraph/sentence/word boundaries, preserving every character.
        cut = max(text.rfind('\n', 0, limit), text.rfind('. ', 0, limit))
        if cut < limit // 2:
            cut = text.rfind(' ', 0, limit)
        if cut < 1:
            cut = limit
        else:
            cut += 1
        chunks.append(text[:cut])
        text = text[cut:]
    if text:
        chunks.append(text)
    return chunks


async def join_speech_audio(parts):
    """Decode/re-encode MP3 parts into one continuous, seekable MP3 file."""
    with tempfile.TemporaryDirectory(prefix='memorial-speech-') as directory:
        root = Path(directory)
        for index, part in enumerate(parts):
            (root / f'part-{index}.mp3').write_bytes(part)
        manifest = root / 'parts.txt'
        manifest.write_text(''.join(f"file 'part-{index}.mp3'\n" for index in range(len(parts))))
        output = root / 'speech.mp3'
        try:
            process = await asyncio.create_subprocess_exec(
                'ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'concat', '-safe', '1',
                '-i', str(manifest), '-vn', '-ar', '44100', '-ac', '1',
                '-c:a', 'libmp3lame', '-b:a', '128k', str(output),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise ValueError('Для озвучки длинной речи на сервере необходим FFmpeg.') from exc
        try:
            await asyncio.wait_for(process.communicate(), timeout=120)
        except BaseException:
            if process.returncode is None:
                process.kill()
            await process.communicate()
            raise
        if process.returncode or not output.exists() or not output.stat().st_size:
            raise ValueError('Не удалось объединить полную речь. Попробуйте озвучить её ещё раз.')
        return output.read_bytes()
