"""
excel_processing.py

This module handles the processing of uploaded Excel files and updates the database accordingly.
"""

import sqlite3

import pandas as pd

from audit import append_audit_event
from guardrails import (
    GuardrailViolation,
    enforce_destructive_action_policy,
    enforce_schema_change_policy,
    quote_identifier,
    review_column_mappings,
)
from prompt import get_column_mapping_prompt_metadata, get_gemini_response
from utils import _normalize_identifier, map_columns


def _read_excel_frame(uploaded_file):
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    return pd.read_excel(uploaded_file)


def preview_excel_import(uploaded_file, db_path, *, emit_audit_event=False):
    """Return the AI-produced column mapping and any pending schema changes."""

    df = _read_excel_frame(uploaded_file)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(PRODUCT)")
        existing_columns = [info[1] for info in cursor.fetchall()]

    column_mappings = map_columns(df.columns, existing_columns, get_gemini_response)
    review = review_column_mappings(column_mappings, existing_columns)
    preview = {
        "dataframe": df,
        "existing_columns": existing_columns,
        "column_mappings": review.sanitized_mapping,
        "proposed_new_columns": list(review.proposed_new_columns),
        "review": review,
    }
    if emit_audit_event:
        append_audit_event(
            db_path,
            "excel_import_preview",
            {
                **get_column_mapping_prompt_metadata(),
                "action": None,
                "uploaded_filename": getattr(uploaded_file, "name", None),
                "column_mappings": review.sanitized_mapping,
                "proposed_new_columns": list(review.proposed_new_columns),
            },
        )
    return preview


def process_excel_file(
    uploaded_file,
    db_path,
    action,
    allow_schema_changes=False,
    allow_destructive_actions=False,
    preview=None,
):
    """
    Processes an uploaded Excel file to update the PRODUCT table in the database.

    Args:
        uploaded_file: The uploaded Excel file.
        db_path (str): The path to the database.
        action (str): The action to perform ("add", "remove", or "modify").
    """
    preview = preview or preview_excel_import(uploaded_file, db_path)
    df = preview["dataframe"]
    column_mappings = preview["column_mappings"]
    audit_details = {
        **get_column_mapping_prompt_metadata(),
        "action": action,
        "uploaded_filename": getattr(uploaded_file, "name", None),
        "column_mappings": column_mappings,
        "proposed_new_columns": list(preview["proposed_new_columns"]),
        "allow_schema_changes": allow_schema_changes,
        "allow_destructive_actions": allow_destructive_actions,
    }
    processed_rows = 0

    try:
        enforce_destructive_action_policy(
            action,
            allow_destructive_actions=allow_destructive_actions,
        )
        enforce_schema_change_policy(
            preview["review"],
            allow_schema_changes=allow_schema_changes,
        )

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Add new columns within the same connection/transaction so that
            # a failure during row processing does not leave the database with
            # orphan columns added by a separate connection.
            existing = {_normalize_identifier(name): name for name in preview["existing_columns"]}
            for db_col in preview["proposed_new_columns"]:
                normalized = _normalize_identifier(db_col)
                if normalized not in existing:
                    col_type = "TEXT"
                    if normalized in {"ID", "STOCK", "QUANTITY", "COUNT"}:
                        col_type = "INTEGER"
                    elif normalized in {"PRICE", "WEIGHT", "COST", "AMOUNT"}:
                        col_type = "REAL"
                    cursor.execute(f'ALTER TABLE PRODUCT ADD COLUMN "{normalized}" {col_type}')
                    existing[normalized] = normalized

            # Process each row in the Excel file
            for _, row in df.iterrows():
                unmapped = [str(col) for col in row.keys() if str(col) not in column_mappings]
                if unmapped:
                    raise ValueError(
                        f"AI column mapping is incomplete — no mapping for: {', '.join(unmapped)}"
                    )
                mapped_row = {column_mappings[str(col)]: value for col, value in row.items()}

                if "NAME" not in mapped_row:
                    raise ValueError(
                        f"Row is missing a NAME mapping; cannot determine which product to {action}."
                    )

                if action == "remove":
                    cursor.execute(
                        f"DELETE FROM PRODUCT WHERE {quote_identifier('NAME')}=?",
                        (mapped_row.get('NAME'),),
                    )
                elif action == "modify":
                    set_clause = ", ".join([f"{quote_identifier(col)}=?" for col in mapped_row.keys()])
                    values = tuple(mapped_row.values())
                    cursor.execute(
                        f"UPDATE PRODUCT SET {set_clause} WHERE {quote_identifier('NAME')}=?",
                        values + (mapped_row.get('NAME'),),
                    )
                else:  # add action (or update if product exists)
                    cursor.execute(
                        f"SELECT * FROM PRODUCT WHERE {quote_identifier('NAME')}=?",
                        (mapped_row.get('NAME'),),
                    )
                    existing_product = cursor.fetchone()
                    if existing_product:
                        set_clause = ", ".join([f"{quote_identifier(col)}=?" for col in mapped_row.keys()])
                        values = tuple(mapped_row.values())
                        cursor.execute(
                            f"UPDATE PRODUCT SET {set_clause} WHERE {quote_identifier('NAME')}=?",
                            values + (mapped_row.get('NAME'),),
                        )
                    else:
                        columns = ", ".join(quote_identifier(col) for col in mapped_row.keys())
                        placeholders = ", ".join(["?" for _ in mapped_row])
                        values = tuple(mapped_row.values())
                        cursor.execute(f"INSERT INTO PRODUCT ({columns}) VALUES ({placeholders})", values)
                processed_rows += 1
        append_audit_event(
            db_path,
            "excel_import_processed",
            {
                **audit_details,
                "processed_rows": processed_rows,
                "status": "success",
            },
        )
    except Exception as exc:
        append_audit_event(
            db_path,
            "excel_import_processed",
            {
                **audit_details,
                "processed_rows": processed_rows,
                "status": "blocked" if isinstance(exc, GuardrailViolation) else "failed",
                "error": str(exc),
            },
        )
        raise
