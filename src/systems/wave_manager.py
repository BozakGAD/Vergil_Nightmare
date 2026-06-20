"""Budget-based enemy wave generation loaded from JSON."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class WaveSettings:
    """Tunable settings for simple budget-based wave generation."""

    max_waves: int
    enemy_costs: dict[str, int]
    base_budget: int
    budget_growth: int
    spawn_margin: int
    spawn_gap: int
    spawn_order: tuple[str, ...]
    inter_wave_delay: float
    spawn_offscreen_distance: int


@dataclass(frozen=True, slots=True)
class EnemySpawn:
    """One enemy id and its horizontal spawn position."""

    enemy_id: str
    x: float
    side: str


class WaveManager:
    """Generate enemy waves by spending a JSON-configured difficulty budget."""

    def __init__(self, settings: WaveSettings) -> None:
        self.settings = settings
        self.current_wave = 0

    @classmethod
    def from_file(cls, path: str | Path = "data/waves.json") -> "WaveManager":
        """Create a wave manager from a JSON settings file."""
        return cls(load_wave_settings(path))

    def next_wave(self, arena_width: int) -> list[EnemySpawn]:
        """Advance to the next wave and return spawn instructions."""
        if self.current_wave >= self.settings.max_waves:
            return []
        self.current_wave += 1
        enemy_ids = self._enemy_ids_for_budget(self._budget_for_wave(self.current_wave))
        return self._place_spawns(enemy_ids, arena_width)

    def _budget_for_wave(self, wave_number: int) -> int:
        return self.settings.base_budget + (wave_number - 1) * self.settings.budget_growth

    def _enemy_ids_for_budget(self, budget: int) -> list[str]:
        enemies: list[str] = []
        remaining = budget
        for enemy_id in self.settings.spawn_order:
            cost = self.settings.enemy_costs[enemy_id]
            while remaining >= cost:
                enemies.append(enemy_id)
                remaining -= cost
        if not enemies:
            cheapest = min(self.settings.enemy_costs, key=self.settings.enemy_costs.__getitem__)
            enemies.append(cheapest)
        return enemies

    def _place_spawns(self, enemy_ids: list[str], arena_width: int) -> list[EnemySpawn]:
        spawns: list[EnemySpawn] = []
        for index, enemy_id in enumerate(enemy_ids):
            side = random.choice(("left", "right"))
            distance = self.settings.spawn_offscreen_distance + index * self.settings.spawn_gap
            x = -distance if side == "left" else arena_width + distance
            spawns.append(EnemySpawn(enemy_id=enemy_id, x=x, side=side))
        return spawns


def load_wave_settings(path: str | Path = "data/waves.json") -> WaveSettings:
    """Load wave generation settings from JSON."""
    raw_data = json.loads(Path(path).read_text(encoding="utf-8"))
    return WaveSettings(
        max_waves=int(raw_data["max_waves"]),
        enemy_costs={str(enemy_id): int(cost) for enemy_id, cost in raw_data["enemy_costs"].items()},
        base_budget=int(raw_data["base_budget"]),
        budget_growth=int(raw_data["budget_growth"]),
        spawn_margin=int(raw_data.get("spawn_margin", 110)),
        spawn_gap=int(raw_data.get("spawn_gap", 82)),
        spawn_order=tuple(str(enemy_id) for enemy_id in raw_data.get("spawn_order", raw_data["enemy_costs"].keys())),
        inter_wave_delay=float(raw_data.get("inter_wave_delay", 0.0)),
        spawn_offscreen_distance=int(raw_data.get("spawn_offscreen_distance", raw_data.get("spawn_margin", 110))),
    )
