"""Database configuration and schema helpers for the inventory app."""

from __future__ import annotations

import random
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).with_name("product_inventory.db")
PRODUCT_TABLE = "PRODUCT"
INVENTORY_VALUE_COLUMN = "STOCK"
PRODUCT_REQUIRED_COLUMNS = (
    "ID",
    "NAME",
    "CATEGORY",
    "BRAND",
    "PRICE",
    INVENTORY_VALUE_COLUMN,
    "SIZE",
    "COLOR",
    "WEIGHT",
    "SPECIFICATIONS",
)

CREATE_PRODUCT_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {PRODUCT_TABLE} (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    NAME VARCHAR(100),
    CATEGORY VARCHAR(50),
    BRAND VARCHAR(50),
    PRICE REAL,
    {INVENTORY_VALUE_COLUMN} INTEGER,
    SIZE VARCHAR(20),
    COLOR VARCHAR(20),
    WEIGHT REAL,
    SPECIFICATIONS TEXT
);
"""


def get_connection(db_path: str | Path = DATABASE_PATH) -> sqlite3.Connection:
    """Return a SQLite connection for the configured product database."""

    return sqlite3.connect(str(db_path))


def validate_product_schema(db_path: str | Path = DATABASE_PATH) -> None:
    """Raise a helpful error when the PRODUCT table schema does not match the app."""

    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (PRODUCT_TABLE,),
        )
        if cursor.fetchone() is None:
            raise RuntimeError(
                f"{db_path} does not contain the required {PRODUCT_TABLE} table."
            )

        cursor.execute(f"PRAGMA table_info({PRODUCT_TABLE})")
        actual_columns = [row[1] for row in cursor.fetchall()]

    missing_columns = [column for column in PRODUCT_REQUIRED_COLUMNS if column not in actual_columns]
    if missing_columns:
        raise RuntimeError(
            "The PRODUCT table schema is out of date. "
            f"Missing columns: {', '.join(missing_columns)}. "
            f"Expected columns: {', '.join(PRODUCT_REQUIRED_COLUMNS)}."
        )


def _build_fake() -> object:
    """Return a Faker-like object, falling back to a lightweight stub if needed."""

    try:
        from faker import Faker as _Faker
    except ImportError:
        class _FallbackFake:
            def word(self) -> str:
                return random.choice(["alpha", "beta", "gamma", "delta"])

            def company(self) -> str:
                return random.choice(["Acme Corp", "Northwind", "Globex", "Initech"])

            def color_name(self) -> str:
                return random.choice(["Red", "Blue", "Green", "Black", "White"])

            def text(self, max_nb_chars: int = 200) -> str:
                return "Sample product description."

        return _FallbackFake()

    return _Faker()


def generate_product_name(fake: object) -> str:
    """Generate a realistic product name for the sample dataset."""

    adjectives = [
        "Premium",
        "Deluxe",
        "Advanced",
        "Smart",
        "Eco-friendly",
        "Compact",
        "Portable",
        "Professional",
    ]
    nouns = ["Device", "Gadget", "Tool", "Appliance", "System", "Kit", "Set", "Solution"]
    return f"{random.choice(adjectives)} {fake.word().capitalize()} {random.choice(nouns)}"


def generate_product_data(num_products: int) -> list[tuple]:
    """Build a sample inventory dataset matching the PRODUCT schema."""

    fake = _build_fake()
    categories = [
        "Electronics",
        "Clothing",
        "Home & Garden",
        "Sports & Outdoors",
        "Books",
        "Toys",
        "Beauty",
        "Food & Beverage",
    ]
    sizes = ["XS", "S", "M", "L", "XL", "XXL", "N/A"]
    product_data = []

    for _ in range(num_products):
        product_data.append(
            (
                generate_product_name(fake),
                random.choice(categories),
                fake.company(),
                round(random.uniform(1.0, 1000.0), 2),
                random.randint(0, 1000),
                random.choice(sizes),
                fake.color_name(),
                round(random.uniform(0.1, 50.0), 2),
                fake.text(max_nb_chars=200),
            )
        )

    return product_data


def initialize_database(db_path: str | Path = DATABASE_PATH, num_products: int = 10000) -> None:
    """Create the sample PRODUCT table and populate it with generated rows."""

    product_data = generate_product_data(num_products)
    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS PRODUCT")
        cursor.execute(CREATE_PRODUCT_TABLE_SQL)
        cursor.executemany(
            f"""
            INSERT INTO {PRODUCT_TABLE}
            (NAME, CATEGORY, BRAND, PRICE, {INVENTORY_VALUE_COLUMN}, SIZE, COLOR, WEIGHT, SPECIFICATIONS)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            product_data,
        )


def print_sample_rows(db_path: str | Path = DATABASE_PATH, limit: int = 10) -> None:
    """Print a few seeded rows to confirm the database contents."""

    with get_connection(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {PRODUCT_TABLE} LIMIT ?", (limit,))
        for row in cursor.fetchall():
            print(row)


if __name__ == "__main__":
    initialize_database()
    print_sample_rows()
    print(f"\nSuccessfully created a product inventory database at {DATABASE_PATH}.")
