"""
Удаляет тестовые мемориалы и пользователей, созданных E2E-тестами Playwright.
Использует прямой psycopg. SET statement_timeout = 0 выполняется ПЕРЕД каждым DELETE,
потому что Supabase PgBouncer (transaction mode) сбрасывает настройки сессии между запросами.

Запуск из backend/:
    source .venv/bin/activate && python cleanup_test_data.py
    python cleanup_test_data.py --dry-run
"""
import os, sys, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

BATCH = 20  # удаляем по N мемориалов за раз, чтобы укладываться в statement_timeout


def exec_no_timeout(conn, sql, params=None):
    """Выполнить SQL с отключённым statement_timeout."""
    conn.execute("SET statement_timeout = 0")
    return conn.execute(sql, params) if params is not None else conn.execute(sql)


def cleanup(dry_run: bool = False):
    import psycopg

    db_url = str(settings.DATABASE_URL)
    conn_str = (db_url
                .replace("postgresql+psycopg://", "postgresql://")
                .replace("postgresql+psycopg2://", "postgresql://"))

    print("Connecting to DB…", flush=True)
    with psycopg.connect(conn_str, autocommit=True) as conn:

        # Находим тестовых пользователей
        rows = exec_no_timeout(conn, """
            SELECT id, email FROM users
            WHERE (email ~ '^test_[0-9]+_[a-z0-9]+@example\\.com$'
                OR email ~ '^e2e_[0-9]+@test\\.com$')
              AND id != 1
            ORDER BY id
        """).fetchall()

        if not rows:
            print("✅ No test users found — DB is clean.", flush=True)
            return

        user_ids = [r[0] for r in rows]
        print(f"{'[DRY RUN] ' if dry_run else ''}Found {len(user_ids)} test users", flush=True)

        if dry_run:
            for uid, email in rows[:20]:
                print(f"  👤 {email} (id={uid})")
            if len(rows) > 20:
                print(f"  … and {len(rows)-20} more")
            mc = exec_no_timeout(conn, """
                SELECT COUNT(DISTINCT memorial_id) FROM memorial_access
                WHERE user_id = ANY(%s)
            """, (user_ids,)).fetchone()[0]
            print(f"\n[DRY RUN] Would delete: {len(user_ids)} users, ~{mc} memorials", flush=True)
            return

        # Находим мемориалы тестовых пользователей
        memorial_ids = [r[0] for r in exec_no_timeout(conn, """
            SELECT DISTINCT memorial_id FROM memorial_access WHERE user_id = ANY(%s)
        """, (user_ids,)).fetchall()]

        print(f"Found {len(memorial_ids)} memorials to delete (batches of {BATCH})", flush=True)

        if memorial_ids:
            steps = [
                ("memories",                     "DELETE FROM memories WHERE memorial_id = ANY(%s)"),
                ("media",                        "DELETE FROM media WHERE memorial_id = ANY(%s)"),
                ("memorial_invites",             "DELETE FROM memorial_invites WHERE memorial_id = ANY(%s)"),
                ("family_relationships (src)",   "DELETE FROM family_relationships WHERE memorial_id = ANY(%s)"),
                ("family_relationships (dst)",   "DELETE FROM family_relationships WHERE related_memorial_id = ANY(%s)"),
                ("memorial_access",              "DELETE FROM memorial_access WHERE memorial_id = ANY(%s)"),
                ("memorials",                    "DELETE FROM memorials WHERE id = ANY(%s)"),
            ]
            for label, sql in steps:
                total = 0
                for i in range(0, len(memorial_ids), BATCH):
                    batch = memorial_ids[i:i + BATCH]
                    total += exec_no_timeout(conn, sql, (batch,)).rowcount
                print(f"  Deleted {total} rows from {label}", flush=True)

        # Удаляем пользователей батчами
        total_users = 0
        for i in range(0, len(user_ids), BATCH):
            batch = user_ids[i:i + BATCH]
            total_users += exec_no_timeout(conn, "DELETE FROM users WHERE id = ANY(%s)", (batch,)).rowcount

        print(f"\n✅ Done: deleted {total_users} users, {len(memorial_ids)} memorials", flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    cleanup(dry_run=args.dry_run)
