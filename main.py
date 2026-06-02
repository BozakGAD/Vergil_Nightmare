"""Executable entry point for Vergil's Nightmare."""

from src.core.game import Game


def main() -> None:
    """Start the game application."""
    Game().run()


if __name__ == "__main__":
    main()
