from __future__ import annotations

import pytest

from guardrails import (
    DestructiveActionApprovalRequired,
    SchemaChangeApprovalRequired,
    SqlGuardrailViolation,
    enforce_destructive_action_policy,
    enforce_schema_change_policy,
    review_column_mappings,
    validate_read_only_sql,
)


def test_validate_read_only_sql_allows_product_selects():
    sql = validate_read_only_sql(
        "WITH low_stock AS (SELECT NAME, STOCK FROM PRODUCT WHERE STOCK < 5) SELECT * FROM low_stock",
        allowed_tables=("PRODUCT",),
    )

    assert sql.startswith("WITH low_stock")


def test_validate_read_only_sql_blocks_dml_hidden_in_with_clause():
    with pytest.raises(SqlGuardrailViolation, match="read-only SQL"):
        validate_read_only_sql(
            "WITH doomed AS (SELECT NAME FROM PRODUCT) DELETE FROM PRODUCT WHERE NAME IN (SELECT NAME FROM doomed)",
            allowed_tables=("PRODUCT",),
        )


def test_validate_read_only_sql_blocks_multiple_statements():
    with pytest.raises(SqlGuardrailViolation, match="single SQL statement"):
        validate_read_only_sql(
            "SELECT * FROM PRODUCT; DROP TABLE PRODUCT",
            allowed_tables=("PRODUCT",),
        )


def test_validate_read_only_sql_blocks_comma_join_bypass():
    with pytest.raises(SqlGuardrailViolation, match="Comma-separated table references"):
        validate_read_only_sql(
            "SELECT PRODUCT.NAME FROM PRODUCT, SQLITE_MASTER",
            allowed_tables=("PRODUCT",),
        )


def test_schema_changes_require_explicit_approval():
    review = review_column_mappings(
        {"Name": "NAME", "Mystery Metric": "mystery metric"},
        existing_columns=("ID", "NAME", "PRICE", "STOCK"),
    )

    assert review.proposed_new_columns == ("MYSTERY_METRIC",)

    with pytest.raises(SchemaChangeApprovalRequired, match="MYSTERY_METRIC"):
        enforce_schema_change_policy(review, allow_schema_changes=False)


def test_destructive_excel_actions_require_explicit_approval():
    with pytest.raises(DestructiveActionApprovalRequired, match="REMOVE"):
        enforce_destructive_action_policy("remove", allow_destructive_actions=False)
