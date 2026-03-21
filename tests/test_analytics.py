from __future__ import annotations

import types
import unittest
from unittest.mock import patch

import analytics


class _FakePreview:
    def to_string(self, index=False):
        return "name  quantity\nWidget 5\nGadget 2"


class _FakeDataFrame:
    columns = ["name", "quantity"]

    def __len__(self):
        return 2

    def head(self, n):
        return _FakePreview()

    def __str__(self):
        return "<fake dataframe>"


class _RecordingClient:
    def __init__(self, response="ok"):
        self.response = response
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return self.response


class AnalyticsTests(unittest.TestCase):
    def test_public_functions_use_client_boundary(self):
        df = _FakeDataFrame()
        client = _RecordingClient()

        with patch.object(analytics, "_get_client", return_value=client):
            self.assertEqual(analytics.generate_insights(df), "ok")
            self.assertEqual(analytics.predict_stock_needs(df), "ok")
            self.assertEqual(
                analytics.categorize_product(df, "Widget", "Useful widget"),
                "ok",
            )
            self.assertEqual(analytics.generate_report(df), "ok")

        self.assertEqual(len(client.prompts), 4)
        self.assertTrue(all("Inventory context:" in prompt for prompt in client.prompts))
        self.assertTrue(any("Columns: name, quantity" in prompt for prompt in client.prompts))
        self.assertTrue(any("Widget" in prompt for prompt in client.prompts))

    def test_gemini_client_rejects_unsupported_sdk_surface(self):
        fake_genai = types.SimpleNamespace(configure=lambda *args, **kwargs: None)

        with self.assertRaisesRegex(
            RuntimeError,
            "must expose configure\\(\\) and GenerativeModel",
        ):
            analytics.GeminiAnalyticsClient(genai_module=fake_genai)

    def test_gemini_client_uses_generative_model(self):
        created_models = []

        class FakeResponse:
            text = "generated text"

        class FakeModel:
            def __init__(self, model_name):
                created_models.append(model_name)

            def generate_content(self, prompt):
                self.last_prompt = prompt
                return FakeResponse()

        fake_genai = types.SimpleNamespace(
            configure=lambda *args, **kwargs: None,
            GenerativeModel=FakeModel,
        )

        client = analytics.GeminiAnalyticsClient(
            model_name="fake-model",
            genai_module=fake_genai,
        )

        self.assertEqual(client.generate("hello"), "generated text")
        self.assertEqual(created_models, ["fake-model"])


if __name__ == "__main__":
    unittest.main()
