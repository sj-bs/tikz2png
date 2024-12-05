from pathlib import Path

import pytest

from tikz2png.directories import Directories


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_directories_creation(temp_dir: Path) -> None:
    directories = Directories.create(base_path=temp_dir)
    assert directories.tikz.exists()
    assert directories.figures.exists()


def test_directories_validation(temp_dir: Path) -> None:
    directories = Directories(tikz=temp_dir / "TikZ", figures=temp_dir / "figures")
    directories.tikz.mkdir()
    directories.figures.mkdir()
    directories.validate()


def test_directories_validation_failure(temp_dir: Path) -> None:
    directories = Directories(
        tikz=temp_dir / "nonexistent", figures=temp_dir / "figures"
    )
    with pytest.raises(FileNotFoundError):
        directories.validate()


def test_directories_validation_permission_error(temp_dir: Path) -> None:
    """Test validation when directories have incorrect permissions."""
    tikz_dir = temp_dir / "TikZ"
    figures_dir = temp_dir / "figures"
    tikz_dir.mkdir(mode=0o000)  # No permissions
    figures_dir.mkdir()

    directories = Directories(tikz=tikz_dir, figures=figures_dir)
    with pytest.raises(PermissionError, match="Cannot read from TikZ directory"):
        directories.validate()

    # Cleanup
    tikz_dir.chmod(0o755)


def test_directories_validation_figures_permission_error(temp_dir: Path) -> None:
    """Test validation when figures directory has incorrect permissions."""
    tikz_dir = temp_dir / "TikZ"
    figures_dir = temp_dir / "figures"
    tikz_dir.mkdir()
    figures_dir.mkdir(mode=0o444)  # Read-only

    directories = Directories(tikz=tikz_dir, figures=figures_dir)
    with pytest.raises(PermissionError, match="Cannot write to figures directory"):
        directories.validate()

    figures_dir.chmod(0o755)


def test_directories_validation_not_directory(temp_dir: Path) -> None:
    """Test validation when path is not a directory."""
    tikz_file = temp_dir / "TikZ"
    figures_dir = temp_dir / "figures"
    tikz_file.touch()
    figures_dir.mkdir()

    directories = Directories(tikz=tikz_file, figures=figures_dir)
    with pytest.raises(NotADirectoryError, match="TikZ path is not a directory"):
        directories.validate()


def test_directories_create_with_invalid_paths() -> None:
    """Test Directories.create with invalid custom paths."""
    with pytest.raises(FileNotFoundError, match="TikZ directory does not exist"):
        Directories.create(tikz_path=Path("/nonexistent"))

    with pytest.raises(FileNotFoundError, match="Output directory does not exist"):
        Directories.create(figures_path=Path("/nonexistent"))


def test_directories_create_default_paths(tmp_path: Path) -> None:
    """Test Directories.create creates default paths."""
    base = tmp_path / "project"

    # Should create Assets/TikZ and Assets/figures
    dirs = Directories.create(base_path=base)

    assert (base / "Assets" / "TikZ").exists()
    assert (base / "Assets" / "figures").exists()
    assert dirs.tikz == base / "Assets" / "TikZ"
    assert dirs.figures == base / "Assets" / "figures"
