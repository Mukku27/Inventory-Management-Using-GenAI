"""Guardrails for AI-generated SQL and AI-assisted schema changes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping

_FORBIDDEN_SQL_KEYWORDS = (
    "ALTER",
    "ATTACH",
    "BEGIN",
    "COMMIT",
    "CREATE",
    "DELETE",
    "DETACH",
    "DROP",
    "INSERT",
    "PRAGMA",
    "REINDEX",
    "RELEASE",
    "REPLACE",
    "ROLLBACK",
    "SAVEPOINT",
    "TRUNCATE",
    "UPDATE",
    "VACUUM",
)
_RESERVED_COLUMN_NAMES = {
    "ALTER",
    "ATTACH",
    "CREATE",
    "DELETE",
    "DROP",
    "FROM",
    "GROUP",
    "INDEX",
    "INSERT",
    "JOIN",
    "ORDER",
    "PRAGMA",
    "SELECT",
    "TABLE",
    "UPDATE",
    "WHERE",
}


class GuardrailViolation(ValueError):
    """Base exception for rejected AI-driven operations."""


class SqlGuardrailViolation(GuardrailViolation):
    """Raised when AI-generated SQL is unsafe to execute."""


class SchemaMappingViolation(GuardrailViolation):
    """Raised when AI-generated schema mappings are invalid."""


class SchemaChangeApprovalRequired(GuardrailViolation):
    """Raised when an import proposes new columns without explicit approval."""

    def __init__(self, proposed_columns: Iterable[str]):
        columns = tuple(proposed_columns)
        joined = ", ".join(columns)
        super().__init__(
            "Schema changes require explicit approval before import. "
            f"Proposed columns: {joined}."
        )
        self.proposed_columns = columns


class DestructiveActionApprovalRequired(GuardrailViolation):
    """Raised when a destructive Excel action lacks explicit approval."""

    def __init__(self, action: str):
        normalized_action = str(action).upper()
        super().__init__(
            "Destructive Excel actions require explicit approval before import. "
            f"Blocked action: {normalized_action}."
        )
        self.action = normalized_action


@dataclass(frozen=True)
class ColumnMappingReview:
    sanitized_mapping: dict[str, str]
    proposed_new_columns: tuple[str, ...]


def normalize_identifier(value: str) -> str:
    """Return a conservative SQLite identifier using only uppercase ASCII tokens."""

    return re.sub(r"[^A-Z0-9]+", "_", str(value).upper()).strip("_")


def quote_identifier(value: str) -> str:
    """Safely quote a sanitized SQLite identifier."""

    normalized = normalize_identifier(value)
    if not normalized:
        raise SchemaMappingViolation("Column names must contain at least one alphanumeric character.")
    return f'"{normalized}"'


def _strip_string_literals(sql: str) -> str:
    return re.sub(r"'(?:''|[^'])*'", "''", sql)


def _matches_keyword(sql: str, start: int, keyword: str) -> bool:
    end = start + len(keyword)
    return (
        sql.startswith(keyword, start)
        and (start == 0 or not (sql[start - 1].isalnum() or sql[start - 1] == "_"))
        and (end == len(sql) or not (sql[end].isalnum() or sql[end] == "_"))
    )


def _has_top_level_comma_join(sql: str) -> bool:
    clause_boundaries = (
        "WHERE",
        "GROUP",
        "ORDER",
        "LIMIT",
        "UNION",
        "EXCEPT",
        "INTERSECT",
        "HAVING",
        "WINDOW",
    )
    depth = 0
    in_from_clause = False
    index = 0

    while index < len(sql):
        char = sql[index]
        if char == "(":
            depth += 1
            index += 1
            continue
        if char == ")":
            depth = max(depth - 1, 0)
            index += 1
            continue

        if depth == 0:
            matched_boundary = next(
                (keyword for keyword in clause_boundaries if _matches_keyword(sql, index, keyword)),
                None,
            )
            if matched_boundary is not None:
                in_from_clause = False
                index += len(matched_boundary)
                continue
            if _matches_keyword(sql, index, "FROM") or _matches_keyword(sql, index, "JOIN"):
                in_from_clause = True
                index += 4
                continue
            if in_from_clause and char == ",":
                return True

        index += 1

    return False


def _extract_cte_names(sql: str) -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(
            r"(?:\bWITH\b|,)\s*([A-Z_][A-Z0-9_]*)\s*(?:\([^)]*\))?\s+AS\s*\(",
            sql,
        )
    }


def validate_read_only_sql(sql: str, allowed_tables: Iterable[str]) -> str:
    """Allow only single-statement, read-only queries over approved tables."""

    candidate = sql.strip()
    if not candidate:
        raise SqlGuardrailViolation("The model did not return a SQL statement.")

    sql_without_literals = _strip_string_literals(candidate)
    if "--" in sql_without_literals or "/*" in sql_without_literals:
        raise SqlGuardrailViolation("SQL comments are not allowed in AI-generated queries.")

    stripped = candidate.rstrip()
    if ";" in stripped.rstrip(";"):
        raise SqlGuardrailViolation("Only a single SQL statement may be executed.")
    candidate = stripped.rstrip(";").strip()

    normalized = re.sub(r"\s+", " ", _strip_string_literals(candidate)).upper()
    if _has_top_level_comma_join(normalized):
        raise SqlGuardrailViolation("Comma-separated table references are not allowed.")

    if not normalized.startswith(("SELECT", "WITH")):
        raise SqlGuardrailViolation("Only read-only SELECT queries are allowed.")

    keyword_pattern = r"\b(?:{})\b".format("|".join(_FORBIDDEN_SQL_KEYWORDS))
    if re.search(keyword_pattern, normalized):
        raise SqlGuardrailViolation("Only read-only SQL is allowed for AI-generated queries.")

    allowed_table_names = {normalize_identifier(table) for table in allowed_tables}
    cte_names = _extract_cte_names(normalized)
    referenced_tables = {
        match.group(1)
        for match in re.finditer(r"\b(?:FROM|JOIN)\s+([A-Z_][A-Z0-9_]*)", normalized)
    }
    external_tables = referenced_tables - cte_names
    if not external_tables:
        raise SqlGuardrailViolation("AI-generated SQL must read from an approved inventory table.")

    disallowed_tables = external_tables - allowed_table_names
    if disallowed_tables:
        joined = ", ".join(sorted(disallowed_tables))
        raise SqlGuardrailViolation(
            f"AI-generated SQL referenced disallowed tables: {joined}."
        )

    return candidate


def review_column_mappings(
    column_mappings: Mapping[str, str],
    existing_columns: Iterable[str],
) -> ColumnMappingReview:
    """Normalize mapped column names and identify proposed schema changes."""

    existing_lookup = {
        normalize_identifier(column): str(column)
        for column in existing_columns
    }
    sanitized_mapping: dict[str, str] = {}
    proposed_new_columns: list[str] = []

    for excel_column, raw_column in column_mappings.items():
        normalized = normalize_identifier(raw_column)
        if not normalized:
            raise SchemaMappingViolation(
                f"Excel column '{excel_column}' mapped to an empty database column name."
            )
        if normalized.startswith("SQLITE_") or normalized in _RESERVED_COLUMN_NAMES:
            raise SchemaMappingViolation(
                f"Excel column '{excel_column}' mapped to the reserved column name '{normalized}'."
            )

        sanitized_mapping[str(excel_column)] = existing_lookup.get(normalized, normalized)
        if normalized not in existing_lookup and normalized not in proposed_new_columns:
            proposed_new_columns.append(normalized)

    return ColumnMappingReview(
        sanitized_mapping=sanitized_mapping,
        proposed_new_columns=tuple(proposed_new_columns),
    )


def enforce_schema_change_policy(
    review: ColumnMappingReview,
    *,
    allow_schema_changes: bool,
) -> None:
    """Reject AI-driven schema changes unless the caller has approved them."""

    if review.proposed_new_columns and not allow_schema_changes:
        raise SchemaChangeApprovalRequired(review.proposed_new_columns)


def enforce_destructive_action_policy(
    action: str,
    *,
    allow_destructive_actions: bool,
) -> None:
    """Reject destructive Excel actions unless the caller has approved them."""

    if str(action).lower() in {"remove", "modify"} and not allow_destructive_actions:
        raise DestructiveActionApprovalRequired(action)
