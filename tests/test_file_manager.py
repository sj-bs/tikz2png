import time
from pathlib import Path
from unittest.mock import Mock

from rich.console import Console

from tikz2png.converter import FileManager


def test_needs_update_when_png_missing(temp_dir: Path) -> None:
    """Test update detection when PNG file is missing."""
    mock_console = Mock(spec=Console)
    file_manager = FileManager(console=mock_console)
    tex_file = temp_dir / "test.tex"
    png_file = temp_dir / "test.png"
    tex_file.touch()

    result = file_manager.needs_update(tex_file, png_file)
    assert result is True
    mock_console.print.assert_called_once_with("🆕 [cyan]Will generate:[/] test.png")


def test_needs_update_when_tex_newer(temp_dir: Path) -> None:
    """Test update detection when TeX file is newer than PNG."""
    mock_console = Mock(spec=Console)
    file_manager = FileManager(console=mock_console)
    tex_file = temp_dir / "test.tex"
    png_file = temp_dir / "test.png"
    png_file.touch()
    time.sleep(0.1)
    tex_file.touch()

    assert file_manager.needs_update(tex_file, png_file) is True


def test_needs_update_when_png_up_to_date(temp_dir: Path) -> None:
    """Test update detection when PNG file is current."""
    mock_console = Mock(spec=Console)
    file_manager = FileManager(console=mock_console)
    tex_file = temp_dir / "test.tex"
    png_file = temp_dir / "test.png"
    tex_file.touch()
    time.sleep(0.1)
    png_file.touch()

    result = file_manager.needs_update(tex_file, png_file)
    assert result is False
    mock_console.print.assert_called_once_with(
        "\n⏭️  [yellow]Skipping:[/] test.tex (PNG is up to date)"
    )


def test_cleanup_auxiliary_files(temp_dir: Path) -> None:
    """Test removal of auxiliary files after compilation."""
    mock_console = Mock(spec=Console)
    file_manager = FileManager(console=mock_console)
    base_path = temp_dir / "test"
    aux_files = [base_path.with_suffix(ext) for ext in [".aux", ".log", ".pdf"]]
    for file in aux_files:
        file.touch()

    file_manager.cleanup_auxiliary_files(base_path)

    for file in aux_files:
        assert not file.exists()
    assert mock_console.print.call_count == len(aux_files)
