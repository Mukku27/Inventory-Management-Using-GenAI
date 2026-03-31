from __future__ import annotations

import json
from pathlib import Path

from audit import append_audit_event, get_audit_log_path
from prompt import (
    COLUMN_MAPPING_PROMPT_NAME,
    COLUMN_MAPPING_PROMPT_VERSION,
    SQL_GENERATION_PROMPT_NAME,
    SQL_GENERATION_PROMPT_VERSION,
    build_column_mapping_prompt,
    build_sql_generation_prompt,
)
from utils import map_columns


def test_append_audit_event_writes_jsonl_next_to_database(tmp_path: Path):
    db_path = tmp_path / "inventory.db"
    db_path.write_text("", encoding="utf-8")

    audit_path = append_audit_event(
        db_path,
        "sql_query_review",
        {"status": "executed", "prompt_version": "v1"},
    )

    assert audit_path == get_audit_log_path(db_path)
    payload = json.loads(audit_path.read_text(encoding="utf-8").strip())
    assert payload["event_type"] == "sql_query_review"
    assert payload["details"]["status"] == "executed"
    assert payload["details"]["prompt_version"] == "v1"
    assert "timestamp" in payload


def test_build_sql_generation_prompt_is_versioned():
    prompt = build_sql_generation_prompt("PRODUCT(ID, NAME)", "List all products")

    assert f"Prompt name: {SQL_GENERATION_PROMPT_NAME}" in prompt
    assert f"Prompt version: {SQL_GENERATION_PROMPT_VERSION}" in prompt


def test_build_column_mapping_prompt_is_versioned():
    prompt = build_column_mapping_prompt(["Name", "Price"], ["NAME", "PRICE"])

    assert f"Prompt name: {COLUMN_MAPPING_PROMPT_NAME}" in prompt
    assert f"Prompt version: {COLUMN_MAPPING_PROMPT_VERSION}" in prompt


def test_map_columns_uses_versioned_prompt_builder():
    captured = {}

    def fake_response(prompt: str) -> str:
        captured["prompt"] = prompt
        return '{"Name": "NAME", "Price": "PRICE"}'

    mapping = map_columns(["Name", "Price"], ["NAME", "PRICE"], fake_response)

    assert mapping == {"Name": "NAME", "Price": "PRICE"}
    assert f"Prompt name: {COLUMN_MAPPING_PROMPT_NAME}" in captured["prompt"]
    assert f"Prompt version: {COLUMN_MAPPING_PROMPT_VERSION}" in captured["prompt"]
