"""Runtime settings loaded from JSON configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class WindowSettings:
    """Window-specific settings."""

    width: int
    height: int
    fps: int
    title: str
    icon_path: str | None
    taskbar_app_id: str | None


@dataclass(frozen=True, slots=True)
class AssetSettings:
    """Paths to optional visual assets."""

    main_menu_background: str | None
    title_placeholder_image: str | None
    game_background: str | None


@dataclass(frozen=True, slots=True)
class GameSettings:
    """Top-level game settings."""

    window: WindowSettings
    assets: AssetSettings

    @classmethod
    def from_file(cls, path: str | Path) -> "GameSettings":
        """Load settings from the project JSON file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        window = data["window"]
        assets = data.get("assets", {})
        return cls(
            window=WindowSettings(
                width=int(window["width"]),
                height=int(window["height"]),
                fps=int(window["fps"]),
                title=str(window["title"]),
                icon_path=window.get("icon_path"),
                taskbar_app_id=window.get("taskbar_app_id"),
            ),
            assets=AssetSettings(
                main_menu_background=assets.get("main_menu_background"),
                title_placeholder_image=assets.get("title_placeholder_image"),
                game_background=assets.get("game_background"),
            ),
        )
