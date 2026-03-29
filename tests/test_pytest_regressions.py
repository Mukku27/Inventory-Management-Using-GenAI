from __future__ import annotations

import importlib
import sqlite3
import sys
import types
from pathlib import Path

import pytest

import database
import prompt


class FakeColumns(list):
    def tolist(self):
        return list(self)


class FakeFrame:
    def __init__(self, rows):
        self._rows = list(rows)
        self.columns = FakeColumns(list(self._rows[0].keys()) if self._rows else [])

    def iterrows(self):
        for index, row in enumerate(self._rows):
            yield index, row


@pytest.fixture
def inventory_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "inventory.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE PRODUCT (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                NAME TEXT,
                CATEGORY TEXT,
                BRAND TEXT,
                PRICE REAL,
                STOCK INTEGER,
                SIZE TEXT,
                COLOR TEXT,
                WEIGHT REAL,
                SPECIFICATIONS TEXT
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO PRODUCT
            (NAME, CATEGORY, BRAND, PRICE, STOCK, SIZE, COLOR, WEIGHT, SPECIFICATIONS)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("Widget", "Gadgets", "Acme", 9.99, 12, "M", "Blue", 1.2, "Original widget"),
                ("Gizmo", "Gadgets", "Acme", 19.99, 3, "L", "Black", 1.8, "Second product"),
            ],
        )
        connection.commit()
    return db_path


@pytest.fixture
def excel_processing_module(monkeypatch):
    fake_streamlit = types.ModuleType("streamlit")
    fake_streamlit.write = lambda *args, **kwargs: None

    fake_pandas = types.ModuleType("pandas")
    fake_pandas.read_excel = lambda uploaded_file: None

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "pandas", fake_pandas)
    # Use monkeypatch so the entry is restored after the test, avoiding stale
    # cached modules that imported with fake streamlit/pandas dependencies.
    monkeypatch.delitem(sys.modules, "excel_processing", raising=False)

    module = importlib.import_module("excel_processing")
    # Register the freshly imported module through monkeypatch so teardown
    # removes it and downstream tests start clean.
    monkeypatch.setitem(sys.modules, "excel_processing", module)

    # Isolate the test from utils/prompt: map each Excel column name to its
    # upper-cased equivalent (matching the PRODUCT schema convention) without
    # calling Gemini or the heuristic logic.
    monkeypatch.setattr(module, "map_columns", lambda cols, existing, fn: {c: c.upper() for c in cols})
    monkeypatch.setattr(module, "add_column_to_db", lambda *args, **kwargs: None)

    return module


def test_initialize_database_bootstraps_a_deterministic_schema(monkeypatch, tmp_path: Path):
    seeded_rows = [
        ("Widget", "Gadgets", "Acme", 9.99, 12, "M", "Blue", 1.2, "Original widget"),
        ("Cable", "Accessories", "Acme", 4.5, 20, "N/A", "White", 0.3, "Charging cable"),
    ]

    monkeypatch.setattr(database, "generate_product_data", lambda num_products: list(seeded_rows))

    db_path = tmp_path / "seeded_inventory.db"
    database.initialize_database(db_path, num_products=len(seeded_rows))
    database.validate_product_schema(db_path)

    with sqlite3.connect(db_path) as connection:
        row_count = connection.execute("SELECT COUNT(*) FROM PRODUCT").fetchone()[0]
        total_value = connection.execute("SELECT SUM(PRICE * STOCK) FROM PRODUCT").fetchone()[0]

    assert row_count == len(seeded_rows)
    assert total_value == pytest.approx((9.99 * 12) + (4.5 * 20))


def test_validate_product_schema_raises_when_table_is_absent(tmp_path: Path):
    db_path = tmp_path / "empty.db"
    sqlite3.connect(db_path).close()

    with pytest.raises(RuntimeError, match="does not contain the required"):
        database.validate_product_schema(db_path)


def test_validate_product_schema_raises_on_missing_column(tmp_path: Path):
    db_path = tmp_path / "incomplete.db"
    with sqlite3.connect(db_path) as connection:
        # Create PRODUCT with only a subset of required columns.
        connection.execute("CREATE TABLE PRODUCT (ID INTEGER PRIMARY KEY, NAME TEXT)")
        connection.commit()

    with pytest.raises(RuntimeError, match="Missing columns"):
        database.validate_product_schema(db_path)


def test_process_excel_file_modify_updates_existing_rows(
    excel_processing_module,
    inventory_db: Path,
):
    excel_processing_module.pd.read_excel = lambda uploaded_file: FakeFrame(
        [
            {
                "Name": "Widget",
                "Category": "Premium Gadgets",
                "Price": 12.5,
                "Stock": 20,
                "Color": "Orange",
            }
        ]
    )

    excel_processing_module.process_excel_file(object(), str(inventory_db), "modify")

    with sqlite3.connect(inventory_db) as connection:
        row = connection.execute(
            "SELECT NAME, CATEGORY, PRICE, STOCK, COLOR FROM PRODUCT WHERE NAME = ?",
            ("Widget",),
        ).fetchone()

    assert row == ("Widget", "Premium Gadgets", 12.5, 20, "Orange")


def test_process_excel_file_remove_deletes_matching_rows(
    excel_processing_module,
    inventory_db: Path,
):
    excel_processing_module.pd.read_excel = lambda uploaded_file: FakeFrame([{"Name": "Gizmo"}])

    excel_processing_module.process_excel_file(object(), str(inventory_db), "remove")

    with sqlite3.connect(inventory_db) as connection:
        remaining_names = [row[0] for row in connection.execute("SELECT NAME FROM PRODUCT")]

    assert remaining_names == ["Widget"]


def test_process_excel_file_add_inserts_new_product(
    excel_processing_module,
    inventory_db: Path,
):
    excel_processing_module.pd.read_excel = lambda uploaded_file: FakeFrame(
        [{"Name": "NewWidget", "Category": "Tools", "Price": 5.0, "Stock": 10}]
    )

    excel_processing_module.process_excel_file(object(), str(inventory_db), "add")

    with sqlite3.connect(inventory_db) as connection:
        names = [row[0] for row in connection.execute("SELECT NAME FROM PRODUCT ORDER BY NAME")]

    assert "NewWidget" in names
    assert len(names) == 3  # Widget + Gizmo + NewWidget


def test_process_excel_file_add_upserts_existing_product(
    excel_processing_module,
    inventory_db: Path,
):
    excel_processing_module.pd.read_excel = lambda uploaded_file: FakeFrame(
        [{"Name": "Widget", "Category": "Updated Gadgets", "Price": 15.0, "Stock": 5}]
    )

    excel_processing_module.process_excel_file(object(), str(inventory_db), "add")

    with sqlite3.connect(inventory_db) as connection:
        row = connection.execute(
            "SELECT NAME, CATEGORY, PRICE, STOCK FROM PRODUCT WHERE NAME = ?",
            ("Widget",),
        ).fetchone()
        total_rows = connection.execute("SELECT COUNT(*) FROM PRODUCT").fetchone()[0]

    assert row == ("Widget", "Updated Gadgets", 15.0, 5)
    assert total_rows == 2  # no duplicate inserted


def test_get_gemini_response_uses_mocked_sdk_when_api_key_is_available(monkeypatch):
    calls = []

    class FakeModel:
        def __init__(self, model_name):
            calls.append(("model", model_name))

        def generate_content(self, supplied_prompt):
            calls.append(("prompt", supplied_prompt))
            return types.SimpleNamespace(text="SELECT * FROM PRODUCT")

    fake_genai = types.SimpleNamespace(
        configure=lambda **kwargs: calls.append(("configure", kwargs)),
        GenerativeModel=FakeModel,
    )
    fake_google = types.ModuleType("google")
    fake_google.__path__ = []
    fake_google.generativeai = fake_genai

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.generativeai", fake_genai)

    response = prompt.get_gemini_response("List all products", model_name="fake-model")

    assert response == "SELECT * FROM PRODUCT"
    assert ("configure", {"api_key": "test-key"}) in calls
    assert ("model", "fake-model") in calls
    assert ("prompt", "List all products") in calls


def test_get_gemini_response_falls_back_when_no_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    response = prompt.get_gemini_response("how many products are there")

    assert "SELECT" in response.upper()
