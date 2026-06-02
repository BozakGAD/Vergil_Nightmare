"""Load, validate and save player control bindings."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.control_constants import DEFAULT_CONTROL_BINDINGS, EDITABLE_CONTROLS


class ControlSettings:
    """Mutable control mapping with JSON persistence.

    The game performs normal dictionary lookups during play, so reading the
    current key for an action is O(1). Disk writes only happen when the user
    changes a binding in the settings menu.
    """

    def __init__(self, storage_path: str | Path) -> None:
        self.storage_path = Path(storage_path)
        self._bindings = dict(DEFAULT_CONTROL_BINDINGS)

    @property
    def bindings(self) -> dict[str, str]:
        """Return a copy of current bindings to protect internal state."""
        return dict(self._bindings)

    def get(self, action: str) -> str:
        """Return a key name for an action."""
        return self._bindings[action]

    def set_key(self, action: str, key_name: str) -> None:
        """Change an editable binding in memory."""
        if action not in EDITABLE_CONTROLS:
            raise ValueError(f"Control '{action}' cannot be changed")
        normalized_key = key_name.strip().lower()
        if not normalized_key:
            raise ValueError("Key name cannot be empty")
        self._bindings[action] = normalized_key

    def load(self) -> None:
        """Load bindings from JSON, falling back to defaults for invalid data."""
        if not self.storage_path.exists():
            self.save()
            return

        raw_data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        if not isinstance(raw_data, dict):
            self.save()
            return

        loaded_bindings = raw_data.get("bindings", raw_data)
        if not isinstance(loaded_bindings, dict):
            self.save()
            return

        merged_bindings = dict(DEFAULT_CONTROL_BINDINGS)
        for action, key_name in loaded_bindings.items():
            if action in merged_bindings and isinstance(key_name, str) and key_name.strip():
                merged_bindings[action] = key_name.strip().lower()

        merged_bindings["pause"] = DEFAULT_CONTROL_BINDINGS["pause"]
        self._bindings = merged_bindings
        self.save()

    def save(self) -> None:
        """Persist current bindings to JSON."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"bindings": self._bindings}
        self.storage_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
