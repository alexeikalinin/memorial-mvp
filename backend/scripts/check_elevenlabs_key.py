#!/usr/bin/env python3
"""
Проверить, принимает ли ElevenLabs ваш API ключ из .env.
Запуск: python -m scripts.check_elevenlabs_key
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings

def main():
    key = (settings.ELEVENLABS_API_KEY or "").strip()
    if not key:
        print("ELEVENLABS_API_KEY в .env не задан или пустой.")
        return
    print(f"Ключ задан (длина {len(key)} символов), проверка...")
    import httpx
    r = httpx.get(
        "https://api.elevenlabs.io/v1/user",
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        timeout=10.0,
    )
    if r.status_code == 200:
        print("OK: ключ принят ElevenLabs.")
        return
    if r.status_code == 401:
        print("Ошибка 401: ключ отклонён. Скопируйте ключ заново из https://elevenlabs.io/app/settings/api-key (без пробелов и переносов строк).")
        return
    print(f"Ответ API: {r.status_code} - {r.text[:200]}")

if __name__ == "__main__":
    main()
