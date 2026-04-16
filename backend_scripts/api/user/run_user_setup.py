"""Apply user auth migration and ensure default admin."""

from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.user.service import ensure_default_admin
from api.utils.db_helper import DatabaseHelper


def main() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    sql_path = os.path.join(
        repo_root,
        "database",
        "postgresql",
        "migrations",
        "add_user_profile_and_admin.sql",
    )
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    db = DatabaseHelper()
    try:
        cur = db.conn.cursor()
        cur.execute(sql)
        db.conn.commit()
        cur.close()
        print("User migration applied.")
    finally:
        db.close()

    ensure_default_admin()
    print("Default admin ensured: admin@raahi.com / admin")


if __name__ == "__main__":
    main()

