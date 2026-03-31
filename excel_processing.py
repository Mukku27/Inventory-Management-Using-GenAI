"""
excel_processing.py

This module handles the processing of uploaded Excel files and updates the database accordingly.
"""

import sqlite3

import pandas as pd
import streamlit as st

from audit import append_audit_event
from guardrails import (
    GuardrailViolation,
    enforce_destructive_action_policy,
    enforce_schema_change_policy,
    quote_identifier,
    review_column_mappings,
)
from prompt import get_column_mapping_prompt_metadata, get_gemini_response
from utils import add_column_to_db, map_columns


def _read_excel_frame(uploaded_file):
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    return pd.read_excel(uploaded_file)


def preview_excel_import(uploaded_file, db_path, *, emit_audit_event=False):
    """Return the AI-produced column mapping and any pending schema changes."""

    df = _read_excel_frame(uploaded_file)
    st.write("Column names in the uploaded file:", df.columns.tolist())

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

        for db_col in preview["proposed_new_columns"]:
            add_column_to_db(db_path, db_col)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Process each row in the Excel file
            for _, row in df.iterrows():
                mapped_row = {column_mappings[str(col)]: value for col, value in row.items()}

                if action == "remove":
                    cursor.execute("DELETE FROM PRODUCT WHERE NAME=?", (mapped_row.get('NAME'),))
                elif action == "modify":
                    set_clause = ", ".join([f"{quote_identifier(col)}=?" for col in mapped_row.keys()])
                    values = tuple(mapped_row.values())
                    cursor.execute(f"UPDATE PRODUCT SET {set_clause} WHERE NAME=?", values + (mapped_row.get('NAME'),))
                else:  # add action (or update if product exists)
                    cursor.execute("SELECT * FROM PRODUCT WHERE NAME=?", (mapped_row.get('NAME'),))
                    existing_product = cursor.fetchone()
                    if existing_product:
                        set_clause = ", ".join([f"{quote_identifier(col)}=?" for col in mapped_row.keys()])
                        values = tuple(mapped_row.values())
                        cursor.execute(f"UPDATE PRODUCT SET {set_clause} WHERE NAME=?", values + (mapped_row.get('NAME'),))
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
