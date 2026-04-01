from __future__ import annotations

import pytest

from guardrails import (
    DestructiveActionApprovalRequired,
    SchemaChangeApprovalRequired,
    SqlGuardrailViolation,
    _strip_string_literals,
    enforce_destructive_action_policy,
    enforce_schema_change_policy,
    review_column_mappings,
    validate_read_only_sql,
)


def test_strip_string_literals_neutralises_single_quoted_values():
    assert _strip_string_literals("SELECT 'DELETE' FROM t") == "SELECT '' FROM t"


def test_strip_string_literals_neutralises_double_quoted_identifiers():
    # "col--name" contains -- which must not trigger the comment check.
    assert _strip_string_literals('SELECT "col--name" FROM t') == 'SELECT "" FROM t'
    # "DELETE" as a quoted identifier must not trigger the keyword scanner.
    assert _strip_string_literals('SELECT "DELETE" FROM t') == 'SELECT "" FROM t'


def test_strip_string_literals_handles_escaped_quotes():
    # '' escape inside single-quoted strings
    assert _strip_string_literals("SELECT 'it''s fine' FROM t") == "SELECT '' FROM t"
    # "" escape inside double-quoted identifiers
    assert _strip_string_literals('SELECT "col""name" FROM t') == 'SELECT "" FROM t'


def test_validate_read_only_sql_allows_double_quoted_identifier_with_dash():
    # A column alias containing -- must not be rejected as a comment.
    sql = validate_read_only_sql(
        'SELECT "price--discount" FROM PRODUCT',
        allowed_tables=("PRODUCT",),
    )
    assert "price--discount" in sql


def test_validate_read_only_sql_allows_double_quoted_keyword_as_identifier():
    # A quoted identifier whose name is a reserved word must not trigger the
    # forbidden-keyword scanner.
    sql = validate_read_only_sql(
        'SELECT "DELETE" FROM PRODUCT',
        allowed_tables=("PRODUCT",),
    )
    assert sql  # query passes validation


def test_validate_read_only_sql_blocks_unquoted_forbidden_keyword():
    # The keyword scanner must still catch an unquoted forbidden keyword that
    # is not inside quotes (use a CTE shape to reach the keyword scan).
    with pytest.raises(SqlGuardrailViolation, match="read-only SQL"):
        validate_read_only_sql(
            "WITH x AS (DELETE FROM PRODUCT) SELECT * FROM PRODUCT",
            allowed_tables=("PRODUCT",),
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


def test_validate_read_only_sql_blocks_derived_table_comma_join_bypass():
    with pytest.raises(SqlGuardrailViolation, match="Comma-separated table references"):
        validate_read_only_sql(
            "SELECT * FROM (SELECT * FROM PRODUCT) product_rows, SQLITE_MASTER",
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
