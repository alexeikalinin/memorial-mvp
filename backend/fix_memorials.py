#!/usr/bin/env python3
"""
Восстанавливает мемориалы: портреты + семейное дерево.

Что делает:
  1. Удаляет дубликаты мемориалов (id=11, id=12)
  2. Загружает портреты из uploads/ и устанавливает как обложки
  3. Восстанавливает семейные связи

Структура семей:
    МОРОЗОВЫ                  КОВАЛЁВЫ
    Иван(3) + Анна(4)         Фёдор(7) + Прасковья(8)
          |                         |
     Николай(5) Мария(6)       Пётр(9) Людмила(10)
          |______________×__________|
                         |
                 Светлана(20) Александр(21)
"""

import sys
import os
import requests
import glob

BASE_URL = os.environ.get("SEED_BASE_URL", "http://localhost:8000/api/v1")
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")

# Проверка сервера
print("Проверяем сервер...")
try:
    r = requests.get(f"{BASE_URL}/memorials/", timeout=30)
    memorials = r.json()
    print(f"Сервер доступен. Мемориалов: {len(memorials)}")
except Exception as e:
    print(f"Сервер недоступен: {e}")
    sys.exit(1)

# ──────────────────────────────────────────────
# 1. Удаляем дубликаты
# ──────────────────────────────────────────────
DUPLICATES = [11, 12]
print("\n=== Удаляем дубликаты ===")
for mid in DUPLICATES:
    r = requests.delete(f"{BASE_URL}/memorials/{mid}", timeout=30)
    if r.status_code == 204:
        print(f"  ✓ Удалён мемориал id={mid}")
    elif r.status_code == 404:
        print(f"  – Мемориал id={mid} уже не существует")
    else:
        print(f"  ✗ Ошибка удаления id={mid}: {r.status_code} {r.text[:80]}")

# ──────────────────────────────────────────────
# 2. Загружаем портреты
# ──────────────────────────────────────────────
# (current_memorial_id, portrait_N, gender, num, имя)
# Portrait N = порядковый номер в seed_photos.py (файлы называются portrait_N_gender_num.jpg)
PORTRAITS = [
    (3,  1, "men",   60,  "Иван Морозов"),
    (4,  2, "women", 64,  "Анна Морозова"),
    (5,  3, "men",   44,  "Николай Морозов"),
    (6,  4, "women", 52,  "Мария Лебедева"),
    (7,  5, "men",   72,  "Фёдор Ковалёв"),
    (8,  6, "women", 73,  "Прасковья Ковалёва"),
    (9,  7, "men",   48,  "Пётр Ковалёв"),
    (10, 8, "women", 46,  "Людмила Морозова"),
    (20, 9, "women", 22,  "Светлана Морозова"),
    (21, 10,"men",   26,  "Александр Морозов"),
]

print("\n=== Загружаем портреты ===")
for memorial_id, portrait_n, gender, num, name in PORTRAITS:
    # Ищем файл в uploads/ по паттерну *_portrait_N_gender_num.jpg
    pattern = os.path.join(UPLOADS_DIR, f"*_portrait_{portrait_n}_{gender}_{num}.jpg")
    matches = glob.glob(pattern)

    if not matches:
        print(f"  ✗ [{memorial_id}] {name}: файл не найден (pattern={pattern})")
        continue

    file_path = matches[0]
    filename = f"portrait_{portrait_n}_{gender}_{num}.jpg"

    print(f"  [{memorial_id}] {name}...", end=" ", flush=True)

    # Проверяем, нет ли уже медиа у мемориала
    existing = requests.get(f"{BASE_URL}/memorials/{memorial_id}/media", timeout=30).json()
    if existing:
        print(f"уже есть {len(existing)} медиа, пропускаем загрузку")
        # Но всё равно устанавливаем обложку если нет
        info = requests.get(f"{BASE_URL}/memorials/{memorial_id}", timeout=30).json()
        if not info.get("cover_photo_id"):
            first_media_id = existing[0]["id"]
            cr = requests.patch(
                f"{BASE_URL}/memorials/{memorial_id}/cover",
                json={"media_id": first_media_id},
                timeout=30,
            )
            if cr.ok:
                print(f"  → обложка установлена (media_id={first_media_id}) ✓")
        continue

    with open(file_path, "rb") as f:
        files = {"file": (filename, f, "image/jpeg")}
        upload_r = requests.post(
            f"{BASE_URL}/memorials/{memorial_id}/media/upload",
            files=files,
            timeout=60,
        )

    if not upload_r.ok:
        print(f"ОШИБКА загрузки: {upload_r.status_code} {upload_r.text[:100]}")
        continue

    media_id = upload_r.json()["id"]
    print(f"загружено (media_id={media_id}),", end=" ", flush=True)

    cover_r = requests.patch(
        f"{BASE_URL}/memorials/{memorial_id}/cover",
        json={"media_id": media_id},
        timeout=30,
    )
    if cover_r.ok:
        print("обложка установлена ✓")
    else:
        print(f"обложка НЕ установлена: {cover_r.status_code} {cover_r.text[:80]}")

# ──────────────────────────────────────────────
# 3. Семейные связи
# ──────────────────────────────────────────────
def link(a_id: int, b_id: int, rel_type: str, notes: str = None):
    payload = {"related_memorial_id": b_id, "relationship_type": rel_type}
    if notes:
        payload["notes"] = notes
    r = requests.post(f"{BASE_URL}/family/memorials/{a_id}/relationships", json=payload, timeout=30)
    if r.ok:
        print(f"  ✓ {a_id} →[{rel_type}]→ {b_id}")
    elif "already exists" in r.text or "already exists" in str(r.text).lower():
        print(f"  – {a_id} →[{rel_type}]→ {b_id} (уже существует)")
    else:
        print(f"  ✗ {a_id} →[{rel_type}]→ {b_id}: {r.status_code} {r.text[:80]}")

print("\n=== Восстанавливаем семейные связи ===")

# Морозовы поколение 1: Иван(3) + Анна(4)
print("\n-- Иван + Анна (супруги) --")
link(3, 4, "spouse")
link(4, 3, "spouse")

# Дети Ивана и Анны
print("\n-- Дети Ивана и Анны --")
link(3, 5, "parent")  # Иван → Николай
link(3, 6, "parent")  # Иван → Мария
link(4, 5, "parent")  # Анна → Николай
link(4, 6, "parent")  # Анна → Мария
link(5, 3, "child")   # Николай → Иван
link(5, 4, "child")   # Николай → Анна
link(6, 3, "child")   # Мария → Иван
link(6, 4, "child")   # Мария → Анна

# Ковалёвы поколение 1: Фёдор(7) + Прасковья(8)
print("\n-- Фёдор + Прасковья (супруги) --")
link(7, 8, "spouse")
link(8, 7, "spouse")

# Дети Фёдора и Прасковьи
print("\n-- Дети Фёдора и Прасковьи --")
link(7, 9,  "parent")  # Фёдор → Пётр
link(7, 10, "parent")  # Фёдор → Людмила
link(8, 9,  "parent")  # Прасковья → Пётр
link(8, 10, "parent")  # Прасковья → Людмила
link(9,  7, "child")   # Пётр → Фёдор
link(9,  8, "child")   # Пётр → Прасковья
link(10, 7, "child")   # Людмила → Фёдор
link(10, 8, "child")   # Людмила → Прасковья

# Брак поколения 2: Николай(5) + Людмила(10)
print("\n-- Николай + Людмила (брак двух семей) --")
link(5, 10, "spouse")
link(10, 5, "spouse")

# Дети Николая и Людмилы
print("\n-- Дети Николая и Людмилы --")
link(5,  20, "parent")  # Николай → Светлана
link(5,  21, "parent")  # Николай → Александр
link(10, 20, "parent")  # Людмила → Светлана
link(10, 21, "parent")  # Людмила → Александр
link(20, 5,  "child")   # Светлана → Николай
link(20, 10, "child")   # Светлана → Людмила
link(21, 5,  "child")   # Александр → Николай
link(21, 10, "child")   # Александр → Людмила

# Сиблинги (братья/сёстры)
print("\n-- Сиблинги --")
link(5, 6,   "sibling")  # Николай ↔ Мария
link(6, 5,   "sibling")
link(9, 10,  "sibling")  # Пётр ↔ Людмила
link(10, 9,  "sibling")
link(20, 21, "sibling")  # Светлана ↔ Александр
link(21, 20, "sibling")

print("\n✅ Готово! Откройте http://localhost:5173")
