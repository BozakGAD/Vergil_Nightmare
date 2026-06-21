"""Optional pygame sprite animation loading helpers."""

from __future__ import annotations

from pathlib import Path

import pygame

from src.core.gameplay_config import AnimationSettings, SpriteSettings


def load_animation_frames(settings: SpriteSettings) -> dict[str, list[pygame.Surface]]:
    """Load animation frames from configured folders when files exist."""
    if not settings.root:
        return {}
    root = Path(settings.root)
    if not root.exists():
        return {}

    animations: dict[str, list[pygame.Surface]] = {}
    for animation_name, animation in settings.animations.items():
        frames = _load_frames(root, animation, settings.scale)
        if frames:
            animations[animation_name] = frames
    return animations


def _load_frames(root: Path, animation: AnimationSettings, scale: int) -> list[pygame.Surface]:
    folder = root / animation.folder
    if not folder.exists():
        return []

    frames: list[pygame.Surface] = []
    for frame_path in sorted(folder.glob("*.png"), key=lambda path: int(path.stem) if path.stem.isdigit() else path.stem):
        frame = pygame.image.load(frame_path).convert_alpha()
        if scale != 1:
            size = (frame.get_width() * scale, frame.get_height() * scale)
            frame = pygame.transform.scale(frame, size)
        frames.append(frame)
    return frames
