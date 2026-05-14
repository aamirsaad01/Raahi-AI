"""Apply chat table migration."""

from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.db_helper import DatabaseHelper


def main() -> None:
    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    sql_path = os.path.join(
        repo_root,
        "database",
        "postgresql",
        "schema",
        "09_chat.sql",
    )
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    db = DatabaseHelper()
    try:
        cur = db.conn.cursor()
        cur.execute(sql)
        db.conn.commit()
        cur.close()
        print("Chat tables migration applied.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

