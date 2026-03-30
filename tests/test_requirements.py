from __future__ import annotations

import pathlib
import sys
import tomllib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def _requirement_names() -> list[str]:
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]
    requirement_names = []

    for dependency in dependencies:
        requirement_name = dependency.split(";", 1)[0].strip()
        requirement_name = requirement_name.split("[", 1)[0]

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
                "pyproject.toml should only include pip-installable packages. "
                f"Found standard-library modules: {', '.join(listed_stdlib_modules)}"
            ),
        )


if __name__ == "__main__":
    unittest.main()
