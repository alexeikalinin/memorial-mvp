#!/usr/bin/env python3
"""
Показать все голоса ElevenLabs, доступные для вашего API-ключа.
На бесплатном тарифе библиотечные голоса (Rachel, Adam) по API недоступны — используйте
кастомные голоса из VoiceLab. Создайте женский и мужской голос, скопируйте их voice_id в .env:
  ELEVENLABS_VOICE_ID_FEMALE=<id женского>
  ELEVENLABS_VOICE_ID_MALE=<id мужского>

Запуск: python -m scripts.list_elevenlabs_voices
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings

def main():
    if not settings.ELEVENLABS_API_KEY:
        print("Задайте ELEVENLABS_API_KEY в backend/.env")
        return
    import httpx
    r = httpx.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": settings.ELEVENLABS_API_KEY, "Content-Type": "application/json"},
        timeout=15.0,
    )
    if r.status_code != 200:
        print(f"Ошибка API: {r.status_code} - {r.text[:300]}")
        return
    data = r.json()
    voices = data.get("voices") or []
    print(f"Доступно голосов: {len(voices)}\n")
    for v in voices:
        vid = v.get("voice_id") or v.get("id") or ""
        name = v.get("name") or "—"
        labels = v.get("labels") or {}
        gender = labels.get("gender") or "—"
        category = v.get("category") or "—"
        print(f"  {vid}")
        print(f"    name: {name}  gender: {gender}  category: {category}")
        if gender == "female":
            print(f"    → для женского в .env: ELEVENLABS_VOICE_ID_FEMALE={vid}")
        elif gender == "male":
            print(f"    → для мужского в .env: ELEVENLABS_VOICE_ID_MALE={vid}")
        print()
    if not voices:
        print("Нет голосов. Создайте голоса в ElevenLabs VoiceLab (бесплатно до 3 шт.).")

if __name__ == "__main__":
    main()
