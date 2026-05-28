"""Human-readable dependency groups for the project.

The installable dependency list is stored in requirements.txt. This module is a
planning helper that documents why each component is expected to be used.
"""

RUNTIME_REQUIREMENTS = {
    "pygame-ce": "Main game framework: window, input, sprites, sound, and rendering.",
}

DEV_REQUIREMENTS = {
    "pytest": "Unit tests for combat logic, wave generation, saves, and configs.",
    "pytest-cov": "Optional test coverage reports for the final project defense.",
    "ruff": "Fast linting and formatting checks for code cleanliness.",
    "mypy": "Optional static type checks for core game logic.",
}
