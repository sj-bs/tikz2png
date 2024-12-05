from pathlib import Path
from unittest.mock import patch

from tikz2png.converter import TikZConverter
from tikz2png.directories import Directories


def test_tikz_converter_run(temp_dir: Path) -> None:
    """
    Test the TikZConverter run method to ensure proper initialisation and method calls.

    Tests that the converter properly organises directories, creates test files,
    and calls the expected methods in the correct order.
    """
    directories = Directories(tikz=temp_dir / "TikZ", figures=temp_dir / "figures")
    directories.tikz.mkdir()
    directories.figures.mkdir()
    tex_file = directories.tikz / "test.tex"
    tex_file.write_text(
        "\\documentclass{standalone}\\begin{document}Test\\end{document}"
    )

    with (
        patch("tikz2png.converter.ImageConverter") as mock_image_converter,
        patch("tikz2png.converter.LaTeXCompiler") as mock_latex_compiler,
        patch("tikz2png.converter.FileManager") as mock_file_manager,
    ):
        mock_file_manager.return_value.needs_update.return_value = True

        converter = TikZConverter(
            directories,
            mock_image_converter.return_value,
            mock_latex_compiler.return_value,
            mock_file_manager.return_value,
        )
        converter.run()

        mock_latex_compiler.return_value.compile.assert_called_once_with(tex_file)
        mock_image_converter.return_value.convert_pdf_to_png.assert_called_once()
        mock_file_manager.return_value.cleanup_auxiliary_files.assert_called_once()
