import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Directories:
    """Container for project directories."""

    tikz: Path
    figures: Path

    @classmethod
    def create(
        cls,
        base_path: Path = Path(),
        tikz_path: Optional[Path] = None,
        figures_path: Optional[Path] = None,
    ) -> "Directories":
        """Create and return project directories."""
        # Validate custom paths if provided
        if tikz_path and not tikz_path.exists():
            raise FileNotFoundError(f"TikZ directory does not exist: {tikz_path}")
        if figures_path and not figures_path.exists():
            raise FileNotFoundError(f"Output directory does not exist: {figures_path}")

        dirs = cls(
            tikz=tikz_path if tikz_path else (base_path / "Assets" / "TikZ"),
            figures=figures_path
            if figures_path
            else (base_path / "Assets" / "figures"),
        )

        # Only create directories for default paths (# TODO: This should be a prompt)
        if not tikz_path:
            dirs.tikz.mkdir(parents=True, exist_ok=True)
        if not figures_path:
            dirs.figures.mkdir(parents=True, exist_ok=True)

        return dirs

    def validate(self) -> None:
        """Validate that both directories exist and are readable."""
        if not self.tikz.exists():
            raise FileNotFoundError(f"TikZ directory does not exist: {self.tikz}")
        if not self.tikz.is_dir():
            raise NotADirectoryError(f"TikZ path is not a directory: {self.tikz}")
        if not os.access(self.tikz, os.R_OK):
            raise PermissionError(f"Cannot read from TikZ directory: {self.tikz}")
        if not os.access(self.figures, os.W_OK):
            raise PermissionError(f"Cannot write to figures directory: {self.figures}")
