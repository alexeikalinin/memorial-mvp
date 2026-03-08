#!/usr/bin/env python3
"""
Загружает портреты для 10 тестовых мемориалов.
Использует randomuser.me — бесплатные фото без регистрации.

Запуск:
    cd backend && source .venv/bin/activate && python seed_photos.py
"""

import sys
import io
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Каждый персонаж: (memorial_id, gender, portrait_num)
# Подобраны числа для нужного возраста/внешности из randomuser.me/api/portraits
PORTRAITS = [
    # ID  пол      номер  имя (для лога)
    (1,  "men",    60,   "Иван Морозов 1895–1965"),       # пожилой мужчина
    (2,  "women",  64,   "Анна Морозова 1898–1972"),      # пожилая женщина
    (3,  "men",    44,   "Николай Морозов 1920–1985"),    # мужчина ср. возраст
    (4,  "women",  52,   "Мария Лебедева 1923–2001"),     # женщина ср. возраст
    (5,  "men",    72,   "Фёдор Ковалёв 1890–1960"),      # очень пожилой мужчина
    (6,  "women",  73,   "Прасковья Ковалёва 1893–1968"), # очень пожилая женщина
    (7,  "men",    48,   "Пётр Ковалёв 1918–1980"),       # мужчина ср. возраст
    (8,  "women",  46,   "Людмила Морозова 1922–1995"),   # женщина ср. возраст
    (9,  "women",  22,   "Светлана Морозова 1948–2020"),  # молодая женщина
    (10, "men",    26,   "Александр Морозов 1950–2018"),  # молодой мужчина
]


def upload_and_set_cover(memorial_id: int, gender: str, num: int, name: str):
    photo_url = f"https://randomuser.me/api/portraits/{gender}/{num}.jpg"
    print(f"  Скачиваем фото для [{memorial_id}] {name}...", end=" ", flush=True)

    try:
        r = requests.get(photo_url, timeout=10)
        if not r.ok:
            print(f"ОШИБКА загрузки фото: {r.status_code}")
            return
    except Exception as e:
        print(f"ОШИБКА сети: {e}")
        return

    filename = f"portrait_{memorial_id}_{gender}_{num}.jpg"
    files = {"file": (filename, io.BytesIO(r.content), "image/jpeg")}

    upload_r = requests.post(
        f"{BASE_URL}/memorials/{memorial_id}/media/upload",
        files=files,
        data={"media_type": "photo"},
    )
    if not upload_r.ok:
        print(f"ОШИБКА загрузки в API: {upload_r.status_code} {upload_r.text[:100]}")
        return

    media_id = upload_r.json()["id"]
    print(f"загружено (media_id={media_id}),", end=" ", flush=True)

    cover_r = requests.patch(
        f"{BASE_URL}/memorials/{memorial_id}/cover",
        json={"media_id": media_id},
    )
    if cover_r.ok:
        print("обложка установлена ✓")
    else:
        print(f"обложка НЕ установлена: {cover_r.status_code} {cover_r.text[:80]}")


print("Проверяем сервер...")
try:
    requests.get(f"{BASE_URL}/memorials/", timeout=3)
except Exception as e:
    print(f"Сервер недоступен: {e}")
    print("Запустите: cd backend && uvicorn app.main:app --reload --port 8000")
    sys.exit(1)
print("Сервер доступен.\n")

print("=== Загружаем портреты ===")
for memorial_id, gender, num, name in PORTRAITS:
    upload_and_set_cover(memorial_id, gender, num, name)

print("\nГотово! Откройте http://localhost:5173 — у каждого мемориала теперь есть фото.")
