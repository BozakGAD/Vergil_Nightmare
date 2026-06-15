"""Base entities for the arena gameplay prototype."""

from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass(slots=True)
class Entity:
    """Simple rectangular world object with health and a position."""

    x: float
    y: float
    width: int
    height: int
    color: tuple[int, int, int]
    max_health: int
    health: int
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    is_alive: bool = True

    @property
    def rect(self) -> pygame.Rect:
        """Return the current collision rectangle."""
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    @property
    def centerx(self) -> float:
        """Horizontal center used by lightweight AI and combat checks."""
        return self.x + self.width / 2

    @property
    def bottom(self) -> float:
        """Bottom edge used by simple ground placement."""
        return self.y + self.height

    def take_damage(self, amount: int) -> None:
        """Reduce health and mark the entity dead at zero health."""
        if not self.is_alive:
            return
        self.health = max(0, self.health - amount)
        if self.health == 0:
            self.is_alive = False
