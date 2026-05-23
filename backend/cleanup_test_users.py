"""
Удаляет всех пользователей кроме:
  - ID 1  (admin@memorial.app, демо-аккаунт)
  - email 1alexeikalinin1@gmail.com (аккаунт разработчика)
"""
import os, sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set"); sys.exit(1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    keep = conn.execute(text(
        "SELECT id, email FROM users WHERE id = 1 OR email = '1alexeikalinin1@gmail.com'"
    )).fetchall()
    keep_ids = [r[0] for r in keep]
    print("Сохраняем:", [(r[0], r[1]) for r in keep])

    to_delete = conn.execute(text(
        f"SELECT id, email FROM users WHERE id NOT IN ({','.join(str(i) for i in keep_ids)})"
    )).fetchall()

    if not to_delete:
        print("Нет пользователей для удаления."); sys.exit(0)

    print(f"\nБудут удалены ({len(to_delete)}):")
    for r in to_delete: print(f"  id={r[0]}  {r[1]}")

    del_ids = ",".join(str(r[0]) for r in to_delete)

    # Получаем memorial_id всех мемориалов удаляемых юзеров
    memorial_rows = conn.execute(text(
        f"SELECT id FROM memorials WHERE owner_id IN ({del_ids})"
    )).fetchall()
    memorial_ids = ",".join(str(r[0]) for r in memorial_rows) or "0"
    print(f"\nМемориалов к удалению: {len(memorial_rows)}")

    # Удаляем каждую таблицу отдельной транзакцией
    steps = [
        # (описание, SQL)
        ("memories",           f"DELETE FROM memories WHERE memorial_id IN ({memorial_ids})"),
        ("media",              f"DELETE FROM media WHERE memorial_id IN ({memorial_ids})"),
        ("family_relationships", f"DELETE FROM family_relationships WHERE memorial_id IN ({memorial_ids}) OR related_memorial_id IN ({memorial_ids})"),
        ("memorial_invites",   f"DELETE FROM memorial_invites WHERE memorial_id IN ({memorial_ids})"),
        ("memorial_access",    f"DELETE FROM memorial_access WHERE memorial_id IN ({memorial_ids}) OR user_id IN ({del_ids})"),
        ("user_usage",         f"DELETE FROM user_usage WHERE user_id IN ({del_ids})"),
        ("memorials",          f"DELETE FROM memorials WHERE owner_id IN ({del_ids})"),
        ("users",              f"DELETE FROM users WHERE id IN ({del_ids})"),
    ]

conn.close()

for desc, sql in steps:
    try:
        with engine.begin() as c:
            r = c.execute(text(sql))
            print(f"  {desc}: удалено {r.rowcount}")
    except Exception as e:
        print(f"  {desc}: ОШИБКА — {e}")

print("\nГотово.")
