from __future__ import annotations

from pathlib import Path

from app.core.db import db_conn


def main() -> None:
    sql_dir = Path(__file__).resolve().parents[1] / "sql"
    migration_files = sorted(sql_dir.glob("*.sql"))
    if not migration_files:
        print("No SQL migration files found.")
        return

    with db_conn() as conn:
        with conn.cursor() as cur:
            for migration in migration_files:
                print(f"Applying {migration.name} ...")
                sql_text = migration.read_text(encoding="utf-8")
                cur.execute(sql_text)
    print("Migrations applied successfully.")


if __name__ == "__main__":
    main()
