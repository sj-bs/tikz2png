from pathlib import Path

import pytest

from tikz2png.config import Config, create_argument_parser


def test_config_from_args(temp_dir: Path) -> None:
    """Test config creation from command line arguments."""
    tikz_dir = temp_dir / "tikz"
    figures_dir = temp_dir / "figures"
    tikz_dir.mkdir()
    figures_dir.mkdir()

    parser = create_argument_parser()
    args = parser.parse_args(
        [
            "--quiet",
            "--force",
            "--tikz-dir",
            str(tikz_dir),
            "--output-dir",
            str(figures_dir),
        ]
    )
    config = Config.from_args(args)

    assert config.quiet is True
    assert config.force is True
    assert config.tikz_dir == tikz_dir
    assert config.output_dir == figures_dir


def test_config_with_missing_args() -> None:
    parser = create_argument_parser()
    args = parser.parse_args([])
    config = Config.from_args(args)

    assert config.quiet is False
    assert config.force is False
    assert config.tikz_dir is None
    assert config.output_dir is None


def test_config_with_invalid_paths() -> None:
    parser = create_argument_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--tikz-dir", "/nonexistent/path"])
