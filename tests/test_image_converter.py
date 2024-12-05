from pathlib import Path
from unittest.mock import patch

import pytest

from tikz2png.converter import ImageConverter
from tikz2png.errors import ImageMagickError


def test_image_converter_initialisation() -> None:
    """Test that ImageConverter initialises with the correct command based on the
    system."""

    def mock_which(cmd: str) -> str | None:
        return "/usr/bin/convert" if cmd == "convert" else None

    with (
        patch("platform.system", return_value="Linux"),
        patch("shutil.which") as mock_which_patch,
    ):
        mock_which_patch.side_effect = mock_which
        converter = ImageConverter()
        assert converter.command == "convert"


def test_convert_pdf_to_png_success(temp_dir: Path) -> None:
    """Test successful PDF to PNG conversion."""
    pdf_file = temp_dir / "test.pdf"
    png_file = temp_dir / "test.png"
    pdf_file.touch()  # An empty PDF file for testing

    with patch("subprocess.run") as mock_run:
        converter = ImageConverter()
        converter.convert_pdf_to_png(pdf_file, png_file)
        mock_run.assert_called_once()


def test_convert_pdf_to_png_failure(temp_dir: Path) -> None:
    """Test proper error handling when PDF conversion fails."""
    pdf_file = temp_dir / "nonexistent.pdf"
    png_file = temp_dir / "test.png"

    converter = ImageConverter()
    with pytest.raises(ImageMagickError):
        converter.convert_pdf_to_png(pdf_file, png_file)
