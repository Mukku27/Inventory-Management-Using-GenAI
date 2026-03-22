"""
analytics.py

This module contains functions to analyze inventory data using Gemini to generate
insights, predict stock needs, categorize products, and generate comprehensive
reports.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

DEFAULT_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
_MAX_CONTEXT_ROWS = 10

_BASE_ANALYSIS_INSTRUCTION = (
    "You are an expert in data analysis. Help non-technical people understand "
    "inventory data, trends, and operational risks."
)


def _load_generative_ai():
    """Load and validate the installed google-generativeai SDK surface."""
    try:
        import google.generativeai as genai
    except ImportError as exc:  # pragma: no cover - exercised via boundary tests
        raise RuntimeError(
            "google-generativeai is required for analytics features."
        ) from exc

    _validate_generative_ai_module(genai)
    return genai


def _validate_generative_ai_module(genai_module: Any) -> None:
    """Ensure the SDK surface exposes the model APIs this module depends on."""
    if not hasattr(genai_module, "configure") or not hasattr(genai_module, "GenerativeModel"):
        raise RuntimeError(
            "Installed google-generativeai SDK must expose configure() and GenerativeModel."
        )


def _extract_text(response: Any) -> str:
    """Normalize Gemini responses into plain text."""
    if isinstance(response, str):
        return response

    text = getattr(response, "text", None)
    if text:
        return text

    candidates = getattr(response, "candidates", None)
    if candidates:
        parts = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            content_parts = getattr(content, "parts", None) if content else None
            if not content_parts:
                continue
            for part in content_parts:
                part_text = getattr(part, "text", None)
                if part_text:
                    parts.append(part_text)
        if parts:
            return "".join(parts)

    return str(response)


def _build_inventory_context(df: Any) -> str:
    """Create a compact inventory snapshot for the language model."""
    columns = list(getattr(df, "columns", []))
    column_line = f"Columns: {', '.join(map(str, columns))}" if columns else "Columns: (unknown)"

    row_count = None
    try:
        row_count = len(df)
    except TypeError:
        row_count = None

    preview = str(df)
    head = getattr(df, "head", None)
    if callable(head):
        try:
            sample = head(_MAX_CONTEXT_ROWS)
            to_string = getattr(sample, "to_string", None)
            preview = to_string(index=False) if callable(to_string) else str(sample)
        except Exception:
            preview = str(df)

    row_line = f"Row count: {row_count}" if row_count is not None else "Row count: unknown"
    return f"{column_line}\n{row_line}\nSample rows:\n{preview}"


@dataclass
class GeminiAnalyticsClient:
    """Thin adapter around the supported Gemini SDK model abstraction."""

    model_name: str = DEFAULT_MODEL_NAME
    genai_module: Any | None = None

    def __post_init__(self) -> None:
        self._genai = self.genai_module or _load_generative_ai()
        _validate_generative_ai_module(self._genai)
        self._model = self._genai.GenerativeModel(self.model_name)

    def generate(self, prompt: str) -> str:
        response = self._model.generate_content(prompt)
        return _extract_text(response)


def _get_client() -> GeminiAnalyticsClient:
    return GeminiAnalyticsClient()


def _run_analysis(df: Any, task_instruction: str, task_prompt: str, client: GeminiAnalyticsClient | None = None) -> str:
    client = client or _get_client()
    context = _build_inventory_context(df)
    prompt = (
        f"{_BASE_ANALYSIS_INSTRUCTION}\n\n"
        f"{task_instruction}\n\n"
        f"{task_prompt}\n\n"
        f"Inventory context:\n{context}"
    )
    return client.generate(prompt)


def generate_insights(df: Any) -> str:
    """
    Generates key insights from the inventory data.

    Args:
        df: The inventory data.

    Returns:
        str: Generated insights.
    """
    insights_prompt = (
        "Analyze this inventory data and provide key insights about stock levels, "
        "popular categories, and pricing trends."
    )
    return _run_analysis(df, "Focus on actionable inventory insights.", insights_prompt)


def predict_stock_needs(df: Any) -> str:
    """
    Predicts which products are likely to run out of stock in the next month.

    Args:
        df: The inventory data.

    Returns:
        str: Stock predictions.
    """
    prediction_prompt = (
        "Based on the current inventory data, predict which products are likely to "
        "run out of stock in the next month. Consider historical sales data if available."
    )
    return _run_analysis(df, "Focus on stock risk and replenishment timing.", prediction_prompt)


def categorize_product(df: Any, product_name: str, product_description: str) -> str:
    """
    Categorizes a product based on its name and description.

    Args:
        df: The inventory data.
        product_name (str): The product name.
        product_description (str): The product description.

    Returns:
        str: The category of the product.
    """
    categorization_prompt = (
        f"Categorize this product:\nName: {product_name}\nDescription: {product_description}"
    )
    return _run_analysis(df, "Focus on the most appropriate inventory category.", categorization_prompt)


def generate_report(df: Any) -> str:
    """
    Generates a comprehensive inventory report.

    Args:
        df: The inventory data.

    Returns:
        str: The inventory report.
    """
    report_prompt = (
        "Generate a comprehensive inventory report. Include total inventory value, "
        "top-selling products, low stock alerts, and any notable trends."
    )
    return _run_analysis(df, "Produce a concise executive summary.", report_prompt)
