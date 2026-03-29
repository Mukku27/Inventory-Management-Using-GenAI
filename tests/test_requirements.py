from __future__ import annotations

import pathlib
import sys
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIREMENTS_PATH = REPO_ROOT / "requirements.txt"


def _requirement_names() -> list[str]:
    requirement_names = []

    for raw_line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        requirement_name = line.split("[", 1)[0]
        for separator in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            requirement_name = requirement_name.split(separator, 1)[0]

        requirement_names.append(requirement_name.strip().lower())

    return requirement_names


class RequirementsTests(unittest.TestCase):
    def test_requirements_exclude_standard_library_modules(self) -> None:
        stdlib_modules = {module.lower() for module in sys.stdlib_module_names}
        listed_stdlib_modules = sorted(
            requirement_name
            for requirement_name in _requirement_names()
            if requirement_name in stdlib_modules
        )

        self.assertEqual(
            listed_stdlib_modules,
            [],
            (
                "requirements.txt should only include pip-installable packages. "
                f"Found standard-library modules: {', '.join(listed_stdlib_modules)}"
            ),
        )


if __name__ == "__main__":
    unittest.main()
