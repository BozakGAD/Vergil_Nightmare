"""Optional pygame sprite animation loading helpers."""

from __future__ import annotations

from pathlib import Path

import pygame

from src.core.gameplay_config import SpriteSettings


def load_player_animation_frames(settings: SpriteSettings) -> dict[str, list[pygame.Surface]]:
    """Load player animation frames from configured folders when files exist."""
    if not settings.root:
        return {}
    root = Path(settings.root)
    if not root.exists():
        return {}

    animations: dict[str, list[pygame.Surface]] = {}
    for animation_name, relative_folder in settings.animations.items():
        folder = root / relative_folder
        if not folder.exists():
            continue
        frames = []
        for frame_path in sorted(folder.glob("*.png")):
            frame = pygame.image.load(frame_path).convert_alpha()
            if settings.scale != 1:
                size = (frame.get_width() * settings.scale, frame.get_height() * settings.scale)
                frame = pygame.transform.scale(frame, size)
            frames.append(frame)
        if frames:
            animations[animation_name] = frames
    return animations
