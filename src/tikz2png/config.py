import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration for the TikZ converter.

    Attributes:
        quiet: Flag to reduce logging output (default: False)
        force: Flag to force regeneration of all PNGs (default: False)
        tikz_dir: Custom directory for TikZ source files (default: ./Assets/TikZ)
        output_dir: Custom directory for PNG outputs (default: ./Assets/figures)
    """

    quiet: bool
    force: bool
    tikz_dir: Optional[Path]
    output_dir: Optional[Path]

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "Config":
        return cls(
            quiet=args.quiet,
            force=args.force,
            tikz_dir=args.tikz_dir,
            output_dir=args.output_dir,
        )


def validate_path(path: str) -> Path:
    """Validate that a path exists."""
    p = Path(path)
    if not p.exists():
        raise argparse.ArgumentTypeError(f"Path does not exist: {p}")
    return p


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for command-line options.

    Returns:
        ArgumentParser: Configured argument parser for the application
    """
    parser = argparse.ArgumentParser(
        prog="tikz2png",
        description="Convert TikZ diagrams to PNG images with LaTeX and ImageMagick",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Reduce logging verbosity (default: debug logging enabled)",
    )
    parser.add_argument(
        "-f", "--force", action="store_true", help="Force regeneration of all PNGs"
    )
    parser.add_argument(
        "--tikz-dir",
        type=validate_path,
        help="Custom directory for TikZ files (default: ./Assets/TikZ)",
    )
    parser.add_argument(
        "--output-dir",
        type=validate_path,
        help="Custom directory for PNG outputs (default: ./Assets/figures)",
    )
    return parser
