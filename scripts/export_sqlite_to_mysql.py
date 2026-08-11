"""Export SQLite sales.db to a MySQL INSERT script."""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQLITE_PATH = PROJECT_ROOT / "instance" / "sales.db"
OUTPUT_PATH = PROJECT_ROOT / "mysql_data.sql"


def sql_value(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def main() -> None:
    if not SQLITE_PATH.exists():
        raise SystemExit(f"SQLite file not found: {SQLITE_PATH}")

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM sales ORDER BY id").fetchall()
    conn.close()

    lines = [
        "-- Generated from SQLite export",
        "USE sales_db;",
        "",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "TRUNCATE TABLE sales;",
        "SET FOREIGN_KEY_CHECKS = 1;",
        "",
    ]

    if not rows:
        lines.append("-- No rows found in SQLite database.")
    else:
        lines.append(
            "INSERT INTO sales (id, order_date, product, region, quantity, unit_price, customer) VALUES"
        )
        values = []
        for row in rows:
            values.append(
                "("
                f"{row['id']}, "
                f"{sql_value(row['order_date'])}, "
                f"{sql_value(row['product'])}, "
                f"{sql_value(row['region'])}, "
                f"{row['quantity']}, "
                f"{row['unit_price']}, "
                f"{sql_value(row['customer'])}"
                ")"
            )
        lines.append(",\n".join(values) + ";")
        lines.extend(
            [
                "",
                f"-- Imported {len(rows)} row(s) from {SQLITE_PATH}",
                "SELECT COUNT(*) AS total_sales FROM sales;",
            ]
        )

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported {len(rows)} row(s) to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
