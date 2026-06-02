from __future__ import annotations

import json

import pytest

from src.core.control_constants import DEFAULT_CONTROL_BINDINGS
from src.systems.control_settings import ControlSettings


def test_load_creates_default_controls_file(tmp_path):
    controls_path = tmp_path / "controls.json"
    settings = ControlSettings(controls_path)

    settings.load()

    assert settings.bindings == dict(DEFAULT_CONTROL_BINDINGS)
    assert json.loads(controls_path.read_text(encoding="utf-8"))["bindings"] == dict(DEFAULT_CONTROL_BINDINGS)


def test_set_key_saves_and_loads_custom_binding(tmp_path):
    controls_path = tmp_path / "controls.json"
    settings = ControlSettings(controls_path)
    settings.set_key("attack", "U")
    settings.save()

    reloaded = ControlSettings(controls_path)
    reloaded.load()

    assert reloaded.get("attack") == "u"


def test_pause_binding_is_not_editable(tmp_path):
    settings = ControlSettings(tmp_path / "controls.json")

    with pytest.raises(ValueError):
        settings.set_key("pause", "p")


def test_load_keeps_escape_for_pause_even_if_file_changes_it(tmp_path):
    controls_path = tmp_path / "controls.json"
    controls_path.write_text(
        json.dumps({"bindings": {"pause": "p", "teleport": "l"}}),
        encoding="utf-8",
    )
    settings = ControlSettings(controls_path)

    settings.load()

    assert settings.get("pause") == "escape"
    assert settings.get("teleport") == "l"
