from pathlib import Path
from unittest.mock import patch

import pytest

from tikz2png.converter import LaTeXCompiler
from tikz2png.errors import LaTeXError


def test_latex_compiler_initialisation() -> None:
    """Test that LaTeXCompiler initialises with the correct LaTeX command."""
    with patch("shutil.which", return_value="/usr/bin/pdflatex"):
        compiler = LaTeXCompiler()
        assert compiler.latex_command == "pdflatex"


def test_compile_success(temp_dir: Path) -> None:
    """Test successful LaTeX document compilation."""
    tex_file = temp_dir / "test.tex"
    tex_file.write_text("\\documentclass{article}\\begin{document}Hello\\end{document}")

    with patch("subprocess.run") as mock_run:
        compiler = LaTeXCompiler()
        compiler.compile(tex_file)
        mock_run.assert_called_once()


def test_compile_failure(temp_dir: Path) -> None:
    """Test that compilation errors are properly handled and raised."""
    tex_file = temp_dir / "test.tex"
    tex_file.write_text(
        "\\documentclass{article}\\begin{document}\\error\\end{document}"
    )

    compiler = LaTeXCompiler()
    with pytest.raises(LaTeXError):
        compiler.compile(tex_file)
