#!/usr/bin/env python3
"""
Загружает портреты для 21 мемориала из seed_extended.py
Использует randomuser.me — бесплатные фото без регистрации.

Запуск:
    cd backend && source .venv/bin/activate && python seed_photos_extended.py
"""

import sys
import io
import os
import requests

BASE_URL = os.environ.get("SEED_BASE_URL", "http://localhost:8000/api/v1")

# (memorial_id, gender, portrait_num, имя)
# men/women + номер подобраны по возрасту персонажа
PORTRAITS = [
    # РОД МОРОЗОВЫХ
    (1,  "men",    75,  "Василий Морозов 1862–1935"),        # очень пожилой
    (2,  "women",  75,  "Пелагея Морозова 1867–1940"),       # очень пожилая
    (3,  "men",    65,  "Иван Морозов 1892–1965"),           # пожилой
    (4,  "men",    44,  "Николай Морозов 1920–1985"),        # средний возраст
    (5,  "women",  52,  "Мария Ковалёва 1923–2001"),         # средний возраст
    (6,  "women",  22,  "Светлана Морозова 1948–2020"),      # молодая
    (7,  "men",    26,  "Александр Морозов 1950–2018"),      # молодой
    (8,  "women",  18,  "Анна Морозова 1975–"),              # молодая

    # РОД КОВАЛЁВЫХ
    (9,  "men",    72,  "Фёдор Ковалёв 1890–1960"),          # очень пожилой
    (10, "women",  73,  "Агафья Ковалёва 1893–1968"),        # очень пожилая
    (11, "men",    60,  "Пётр Ковалёв 1918–1980"),           # пожилой
    (12, "men",    48,  "Сергей Ковалёв 1921–1999"),         # средний возраст
    (13, "women",  46,  "Людмила Морозова 1924–1995"),       # средний возраст
    (14, "women",  38,  "Алёна Ковалёва 1950–2015"),        # средний возраст
    (15, "women",  30,  "Ирина Власова 1952–2010"),          # средний возраст
    (16, "men",    20,  "Виктор Ковалёв 1974–"),             # молодой

    # РОД ВЛАСОВЫХ
    (17, "women",  15,  "Полина Власова 1978–"),             # молодая
    (18, "men",    55,  "Евгений Власов 1900–1970"),         # пожилой
    (19, "men",    50,  "Борис Борисов 1925–1995"),          # средний возраст
    (20, "women",  42,  "Наталья Власова 1950–2005"),        # средний возраст
    (21, "men",    24,  "Дмитрий Власов 1976–"),             # молодой
]


def upload_and_set_cover(memorial_id: int, gender: str, num: int, name: str):
    photo_url = f"https://randomuser.me/api/portraits/{gender}/{num}.jpg"
    print(f"  [{memorial_id}] {name}...", end=" ", flush=True)

    try:
        r = requests.get(photo_url, timeout=10)
        if not r.ok:
            print(f"ОШИБКА фото: {r.status_code}")
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
        print(f"ОШИБКА загрузки: {upload_r.status_code} {upload_r.text[:80]}")
        return

    media_id = upload_r.json()["id"]

    cover_r = requests.patch(
        f"{BASE_URL}/memorials/{memorial_id}/cover",
        json={"media_id": media_id},
    )
    if cover_r.ok:
        print(f"✓ (media_id={media_id})")
    else:
        print(f"загружено, но обложка не установлена: {cover_r.status_code}")


print("Проверяем сервер...")
try:
    requests.get(f"{BASE_URL}/memorials/", timeout=3)
except Exception as e:
    print(f"Сервер недоступен: {e}")
    print("Запустите: cd backend && uvicorn app.main:app --reload --port 8000")
    sys.exit(1)
print("Сервер доступен.\n")
print("Загружаем портреты...\n")

for args in PORTRAITS:
    upload_and_set_cover(*args)

print(f"\n✅ Готово! Загружено {len(PORTRAITS)} портретов.")
print("Откройте http://localhost:5173 для просмотра")
