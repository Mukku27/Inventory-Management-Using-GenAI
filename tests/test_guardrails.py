from __future__ import annotations

import pytest

from guardrails import (
    DestructiveActionApprovalRequired,
    SchemaChangeApprovalRequired,
    SqlGuardrailViolation,
    _strip_string_literals,
    enforce_destructive_action_policy,
    enforce_schema_change_policy,
    normalize_identifier,
    quote_identifier,
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


def test_validate_read_only_sql_allows_recursive_cte():
    # WITH RECURSIVE: the CTE name must be extracted so the self-reference
    # inside the recursive body is not treated as an external table.
    sql = validate_read_only_sql(
        """
        WITH RECURSIVE counter(n) AS (
            SELECT 1
            UNION ALL
            SELECT n + 1 FROM counter WHERE n < 5
        )
        SELECT p.NAME, c.n FROM PRODUCT p JOIN counter c ON 1 = 1
        """,
        allowed_tables=("PRODUCT",),
    )
    assert sql.strip()


def test_validate_read_only_sql_allows_recursive_cte_without_column_list():
    sql = validate_read_only_sql(
        """
        WITH RECURSIVE ancestors AS (
            SELECT ID, NAME FROM PRODUCT WHERE ID = 1
            UNION ALL
            SELECT p.ID, p.NAME FROM PRODUCT p JOIN ancestors a ON p.ID = a.ID + 1
        )
        SELECT * FROM ancestors
        """,
        allowed_tables=("PRODUCT",),
    )
    assert sql.strip()


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


def test_validate_read_only_sql_blocks_empty_sql():
    with pytest.raises(SqlGuardrailViolation, match="did not return"):
        validate_read_only_sql("", allowed_tables=("PRODUCT",))


def test_validate_read_only_sql_blocks_whitespace_only():
    with pytest.raises(SqlGuardrailViolation, match="did not return"):
        validate_read_only_sql("   ", allowed_tables=("PRODUCT",))


def test_validate_read_only_sql_blocks_exceeding_max_length():
    long_sql = "SELECT * FROM PRODUCT WHERE NAME = '" + "A" * 100_001 + "'"
    with pytest.raises(SqlGuardrailViolation, match="maximum allowed length"):
        validate_read_only_sql(long_sql, allowed_tables=("PRODUCT",))


def test_validate_read_only_sql_blocks_schema_qualified_table():
    with pytest.raises(SqlGuardrailViolation, match="disallowed tables"):
        validate_read_only_sql(
            "SELECT * FROM main.sqlite_master",
            allowed_tables=("PRODUCT",),
        )


def test_validate_read_only_sql_allows_schema_qualified_allowed_table():
    sql = validate_read_only_sql(
        "SELECT * FROM main.PRODUCT",
        allowed_tables=("PRODUCT",),
    )
    assert sql


def test_validate_read_only_sql_blocks_attach_database():
    with pytest.raises(SqlGuardrailViolation, match="read-only"):
        validate_read_only_sql(
            "ATTACH DATABASE ':memory:' AS other",
            allowed_tables=("PRODUCT",),
        )


def test_strip_string_literals_handles_backtick_quoted_identifiers():
    assert _strip_string_literals("SELECT `DELETE` FROM t") == 'SELECT "" FROM t'
    assert _strip_string_literals("SELECT `col--name` FROM t") == 'SELECT "" FROM t'


def test_validate_read_only_sql_allows_backtick_quoted_keyword_as_identifier():
    sql = validate_read_only_sql(
        "SELECT `DELETE` FROM PRODUCT",
        allowed_tables=("PRODUCT",),
    )
    assert sql


def test_validate_read_only_sql_with_empty_allowed_tables():
    with pytest.raises(SqlGuardrailViolation, match="disallowed tables"):
        validate_read_only_sql(
            "SELECT * FROM PRODUCT",
            allowed_tables=(),
        )


def test_validate_read_only_sql_semicolon_inside_string_literal():
    sql = validate_read_only_sql(
        "SELECT * FROM PRODUCT WHERE NAME = 'a;b'",
        allowed_tables=("PRODUCT",),
    )
    assert sql


def test_normalize_identifier_strips_special_chars():
    assert normalize_identifier("hello world!") == "HELLO_WORLD"
    assert normalize_identifier("---") == ""
    assert normalize_identifier("col 1") == "COL_1"


def test_quote_identifier_rejects_empty():
    with pytest.raises(Exception):
        quote_identifier("---")


def test_quote_identifier_normalizes_and_quotes():
    assert quote_identifier("my column") == '"MY_COLUMN"'
