import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Optional
from unittest.mock import Mock, call, create_autospec, patch

import pytest
from rich.progress import TaskID

from tikz2png.config import Config
from tikz2png.converter import (
    FileManager,
    ImageConverter,
    ImageMagickError,
    LaTeXCompiler,
    LaTeXError,
    TikZConverter,
    create_converter,
    extract_latex_errors,
    main,
)
from tikz2png.interfaces import (
    FileManagerInterface,
    ImageConverterInterface,
    LaTeXCompilerInterface,
)


def test_extract_latex_errors_with_error() -> None:
    stderr = """
    This is pdfTeX, Version 3.14159265-2.6-1.40.21
    ! LaTeX Error: File `nonexistent.sty' not found

    Type X to quit or <RETURN> to proceed
    """
    result = extract_latex_errors(stderr)
    assert "LaTeX Error: File `nonexistent.sty' not found" in result


def test_extract_latex_errors_without_error() -> None:
    stderr = "This is pdfTeX, Version 3.14159265-2.6-1.40.21"
    result = extract_latex_errors(stderr)
    assert result == stderr


def test_create_converter_with_invalid_directories() -> None:
    config = Config(
        quiet=False,
        force=False,
        tikz_dir=Path("/nonexistent"),
        output_dir=Path("/nonexistent"),
    )
    with pytest.raises(FileNotFoundError):
        create_converter(config)


def test_imagemagick_not_found():
    """Test ImageMagick command detection when not installed."""
    with patch("shutil.which", return_value=None):
        with pytest.raises(ImageMagickError, match="ImageMagick not found"):
            ImageConverter()


def test_latex_compiler_not_found():
    """Test LaTeX compiler detection when not installed."""
    with patch("shutil.which", return_value=None):
        with pytest.raises(LaTeXError, match="LaTeX compiler not found"):
            LaTeXCompiler()


def test_main_function_error_handling():
    """Test main function error handling."""
    mock_args: Mock = Mock(spec=Any)
    mock_args.quiet = True
    mock_args.force = False
    mock_args.tikz_dir = "/nonexistent"
    mock_args.output_dir = "/nonexistent"

    with (
        patch(
            "argparse.ArgumentParser.parse_args", return_value=mock_args, autospec=True
        ),
        patch("sys.exit", autospec=True) as mock_exit,
    ):
        main()
        mock_exit.assert_called_once_with(1)


def test_imagemagick_command_selection():
    """Test ImageMagick command selection logic."""

    def check_magick(x: str) -> bool:
        return str(x) == "magick.exe"

    def check_convert(x: str) -> bool:
        return str(x) == "convert"

    with (
        patch("platform.system", return_value="Windows", autospec=True),
        patch("shutil.which", side_effect=check_magick, autospec=True),
    ):
        converter = ImageConverter()
        assert converter.command == "magick.exe"

    with (
        patch("platform.system", return_value="Linux", autospec=True),
        patch("shutil.which", side_effect=check_convert, autospec=True),
    ):
        with patch("logging.Logger.warning", autospec=True) as mock_warning:
            converter = ImageConverter()
            assert converter.command == "convert"
            mock_warning.assert_called_once()


def test_file_manager_needs_update(tmp_path: Path) -> None:
    """Test FileManager.needs_update with different scenarios."""

    manager = FileManager()

    tex_file = tmp_path / "test.tex"
    png_file = tmp_path / "test.png"

    # When PNG doesn't exist
    tex_file.touch()
    assert manager.needs_update(tex_file, png_file)

    # When TEX is newer
    png_file.touch()
    time.sleep(1)
    tex_file.touch()  # Updates timestamp to newer
    assert manager.needs_update(tex_file, png_file)

    # When PNG is newer
    tex_file.touch()
    time.sleep(1)
    png_file.touch()  # Makes PNG newer than TEX
    assert not manager.needs_update(tex_file, png_file)


def test_file_manager_cleanup(tmp_path: Path) -> None:
    """Test FileManager.cleanup_auxiliary_files."""
    manager = FileManager()
    base_path = tmp_path / "test.tex"

    # Create aux files
    aux_files = [".aux", ".log", ".pdf"]
    for ext in aux_files:
        (tmp_path / f"test{ext}").touch()

    manager.cleanup_auxiliary_files(base_path)

    for ext in aux_files:
        assert not (tmp_path / f"test{ext}").exists()


def test_image_converter_magick_command(tmp_path: Path) -> None:
    """Test ImageMagick command selection on Unix."""

    def check_magick(x: str) -> Optional[str]:
        return "magick" if x == "magick" else None

    def check_convert(x: str) -> Optional[str]:
        return "convert" if x == "convert" else None

    with patch("platform.system", return_value="Linux"):
        with patch("shutil.which", new=create_autospec(check_magick)):
            converter = ImageConverter()
            assert converter.command == "magick"
        # Fallback
        with patch("shutil.which", side_effect=check_convert):
            converter = ImageConverter()
            assert converter.command == "convert"


def test_image_converter_conversion_error(tmp_path: Path) -> None:
    """Test ImageConverter handling of conversion errors."""
    converter = ImageConverter()
    pdf_file = tmp_path / "test.pdf"
    png_file = tmp_path / "test.png"
    pdf_file.touch()

    error = subprocess.CalledProcessError(1, cmd=[], stderr="error")
    with patch("subprocess.run", side_effect=error):
        with pytest.raises(ImageMagickError, match="Image conversion failed"):
            converter.convert_pdf_to_png(pdf_file, png_file)


def test_tikz_converter_process_file(tmp_path: Path) -> None:
    """Test TikZConverter.process_file with mocked components."""
    directories = Mock()
    directories.figures = tmp_path

    image_converter = create_autospec(ImageConverterInterface)
    latex_compiler = create_autospec(LaTeXCompilerInterface)
    file_manager = create_autospec(FileManagerInterface)

    file_manager.needs_update = Mock(return_value=True)
    latex_compiler.compile = Mock()

    converter = TikZConverter(
        directories=directories,
        image_converter=image_converter,
        latex_compiler=latex_compiler,
        file_manager=file_manager,
    )

    tex_file = tmp_path / "test.tex"
    tex_file.touch()

    # Successful conversion
    assert converter.process_file(tex_file, force=True)
    assert converter.stats["processed"] == 1

    # Failed conversion
    latex_compiler.compile = Mock(side_effect=LaTeXError("Test error"))
    assert not converter.process_file(tex_file, force=True)
    assert converter.stats["failed"] == 1


def test_tikz_converter_run_empty_directory(tmp_path: Path) -> None:
    """Test TikZConverter.run with no tex files."""
    directories = Mock()
    directories.tikz = tmp_path
    directories.figures = tmp_path

    converter = TikZConverter(
        directories=directories,
        image_converter=Mock(),
        latex_compiler=Mock(),
        file_manager=Mock(),
    )

    with patch("logging.Logger.warning") as mock_warning:
        converter.run()
        mock_warning.assert_called_once_with("No .tex files found in Assets/TikZ!")


def test_tikz_converter_run_with_files(tmp_path: Path) -> None:
    """Test TikZConverter.run with tex files."""
    tikz_dir = tmp_path / "tikz"
    tikz_dir.mkdir()
    tex_file = tikz_dir / "test.tex"
    tex_file.touch()

    directories = Mock()
    directories.tikz = tikz_dir
    directories.figures = tmp_path

    image_converter = create_autospec(ImageConverterInterface)
    latex_compiler = create_autospec(LaTeXCompilerInterface)
    file_manager = create_autospec(FileManagerInterface)
    file_manager.needs_update.return_value = True

    converter = TikZConverter(
        directories=directories,
        image_converter=image_converter,
        latex_compiler=latex_compiler,
        file_manager=file_manager,
    )

    with patch("rich.console.Console.print") as mock_print:
        converter.run()
        assert mock_print.call_count >= 2  # Initial panel and summary panel
        latex_compiler.compile.assert_called_once()


def test_file_manager_cleanup_error(tmp_path: Path) -> None:
    """Test FileManager cleanup when permission error occurs."""
    manager = FileManager()
    base_path = tmp_path / "test.tex"

    # Create a file and make the parent directory read-only
    aux_file = tmp_path / "test.aux"
    aux_file.touch()
    tmp_path.chmod(0o555)  # Read and execute only, no write permission

    with patch("rich.console.Console.print") as mock_print:
        manager.cleanup_auxiliary_files(base_path)
        mock_print.assert_called()
        args, _ = mock_print.call_args
        expected_start = f"\n⚠️  [yellow]Failed to remove[/] {aux_file.name}:"
        assert args[0].startswith(expected_start)

    # restore write permissions to allow pytest to clean up
    tmp_path.chmod(0o755)


def test_tikz_converter_with_progress(tmp_path: Path) -> None:
    """Test TikZConverter with progress bar."""
    tikz_dir = tmp_path / "tikz"
    tikz_dir.mkdir()
    tex_file = tikz_dir / "test.tex"
    tex_file.touch()

    directories = Mock()
    directories.tikz = tikz_dir
    directories.figures = tmp_path

    image_converter = create_autospec(ImageConverterInterface)
    latex_compiler = create_autospec(LaTeXCompilerInterface)
    file_manager = create_autospec(FileManagerInterface)

    converter = TikZConverter(
        directories=directories,
        image_converter=image_converter,
        latex_compiler=latex_compiler,
        file_manager=file_manager,
    )

    mock_progress = Mock()
    mock_console = Mock()
    mock_progress.console = mock_console
    task_id = TaskID(1)

    result = converter.process_file(
        tex_file, force=True, task_id=task_id, progress=mock_progress
    )
    assert result is True

    mock_progress.update.assert_called_with(
        task_id, description=f"Processing {tex_file.name}"
    )
    mock_console.print.assert_called_with(
        f"\n✅ [green]Successfully converted:[/] {tex_file.name} -> "
        f"{tex_file.stem}.png"
    )

    expected_calls: list[Any] = [
        call(
            f"\n✅ [green]Successfully converted:[/] {tex_file.name} -> "
            f"{tex_file.stem}.png"
        ),
    ]
    mock_console.print.assert_has_calls(expected_calls, any_order=False)


def test_tikz_converter_error_with_progress(tmp_path: Path) -> None:
    """Test TikZConverter error handling with progress bar."""
    tikz_dir = tmp_path / "tikz"
    tikz_dir.mkdir()
    tex_file = tikz_dir / "test.tex"
    tex_file.touch()

    directories = Mock()
    directories.tikz = tikz_dir
    directories.figures = tmp_path

    image_converter = create_autospec(ImageConverterInterface)
    latex_compiler = create_autospec(LaTeXCompilerInterface)
    file_manager = create_autospec(FileManagerInterface)

    latex_compiler.compile.side_effect = LaTeXError("Test error")

    converter = TikZConverter(
        directories=directories,
        image_converter=image_converter,
        latex_compiler=latex_compiler,
        file_manager=file_manager,
    )

    mock_progress = Mock()
    mock_console = Mock()
    mock_progress.console = mock_console
    task_id = TaskID(1)

    result = converter.process_file(
        tex_file, force=True, task_id=task_id, progress=mock_progress
    )
    assert not result
    mock_console.print.assert_called_with(
        "[red]Error processing " + tex_file.name + ": Test error[/]"
    )


def test_latex_compiler_file_not_found() -> None:
    """Test LaTeXCompiler when input file doesn't exist."""
    compiler = LaTeXCompiler()
    with pytest.raises(FileNotFoundError, match="LaTeX file not found"):
        compiler.compile(Path("nonexistent.tex"))


def test_create_converter_with_quiet_mode() -> None:
    """Test create_converter with quiet mode enabled."""
    config = Config(
        quiet=True,
        force=False,
        tikz_dir=None,
        output_dir=None,
    )

    with patch("tikz2png.directories.Directories.create") as mock_create:
        mock_create.return_value = Mock()
        mock_create.return_value.validate = Mock()

        converter = create_converter(config)
        assert isinstance(converter, TikZConverter)
        mock_create.assert_called_once()


def test_tikz_converter_run_with_exception(tmp_path: Path) -> None:
    """Test TikZConverter.run handles exceptions during processing."""
    tikz_dir = tmp_path / "tikz"
    tikz_dir.mkdir()
    tex_file = tikz_dir / "test.tex"
    tex_file.touch()

    directories = Mock()
    directories.tikz = tikz_dir
    directories.figures = tmp_path

    image_converter = create_autospec(ImageConverterInterface)
    latex_compiler = create_autospec(LaTeXCompilerInterface)
    file_manager = create_autospec(FileManagerInterface)

    latex_compiler.compile.side_effect = LaTeXError("Compilation failed")

    converter = TikZConverter(
        directories=directories,
        image_converter=image_converter,
        latex_compiler=latex_compiler,
        file_manager=file_manager,
    )

    with patch("rich.console.Console.print") as mock_print:
        converter.run()
        mock_print.assert_any_call(
            "[red]Error processing test.tex: Compilation failed[/]"
        )
        assert converter.stats["failed"] == 1


def test_tikz_converter_run_with_partial_failures(tmp_path: Path) -> None:
    """Test TikZConverter.run with some files failing to process."""
    tikz_dir = tmp_path / "tikz"
    tikz_dir.mkdir()
    tex_file1 = tikz_dir / "test1.tex"
    tex_file2 = tikz_dir / "test2.tex"
    tex_file1.touch()
    tex_file2.touch()

    directories = Mock()
    directories.tikz = tikz_dir
    directories.figures = tmp_path

    image_converter = create_autospec(ImageConverterInterface)
    latex_compiler = create_autospec(LaTeXCompilerInterface)
    file_manager = create_autospec(FileManagerInterface)

    # First file processes successfully, second fails
    def compile_side_effect(tex_file: Path) -> None:
        if tex_file.name == "test1.tex":
            return
        else:
            raise LaTeXError("Compilation failed for test2.tex")

    latex_compiler.compile.side_effect = compile_side_effect

    converter = TikZConverter(
        directories=directories,
        image_converter=image_converter,
        latex_compiler=latex_compiler,
        file_manager=file_manager,
    )

    with patch("rich.console.Console.print") as mock_print:
        converter.run()
        # Check that an error message was printed for test2.tex
        mock_print.assert_any_call(
            "[red]Error processing test2.tex: Compilation failed for test2.tex[/]"
        )
        assert converter.stats["processed"] == 1
        assert converter.stats["failed"] == 1


def test_converter_main_with_validation_error() -> None:
    """Test main function when directory validation fails."""
    mock_args = Mock()
    mock_args.quiet = False
    mock_args.force = False
    mock_args.tikz_dir = None
    mock_args.output_dir = None

    with (
        patch("argparse.ArgumentParser.parse_args", return_value=mock_args),
        patch("tikz2png.converter.create_converter") as mock_create,
        patch("sys.exit") as mock_exit,
        patch("rich.console.Console.print") as mock_print,
    ):
        mock_create.side_effect = PermissionError("Cannot write to figures directory")
        main()
        mock_print.assert_called_with(
            "[red bold]❌ Error:[/] Cannot write to figures directory"
        )
        mock_exit.assert_called_once_with(1)


def test_converter_with_logger_setup() -> None:
    """Test logger setup in quiet mode."""
    mock_args = Mock()
    mock_args.quiet = True
    mock_args.force = False
    mock_args.tikz_dir = None
    mock_args.output_dir = None

    with (
        patch("argparse.ArgumentParser.parse_args", return_value=mock_args),
        patch("logging.getLogger") as mock_logger,
        patch("tikz2png.converter.create_converter", side_effect=Exception),
        patch("sys.exit"),
    ):
        main()
        mock_logger.return_value.setLevel.assert_called_once_with(logging.WARNING)


def test_tikz_converter_with_skipped_files(tmp_path: Path) -> None:
    """Test TikZConverter when files don't need updating."""
    tikz_dir = tmp_path / "tikz"
    tikz_dir.mkdir()
    tex_file = tikz_dir / "test.tex"
    tex_file.touch()

    directories = Mock()
    directories.tikz = tikz_dir
    directories.figures = tmp_path

    image_converter = create_autospec(ImageConverterInterface)
    latex_compiler = create_autospec(LaTeXCompilerInterface)
    file_manager = create_autospec(FileManagerInterface)
    file_manager.needs_update.return_value = False

    converter = TikZConverter(
        directories=directories,
        image_converter=image_converter,
        latex_compiler=latex_compiler,
        file_manager=file_manager,
    )

    result = converter.process_file(tex_file)
    assert not result
    assert converter.stats["skipped"] == 1
    assert converter.stats["processed"] == 0
    latex_compiler.compile.assert_not_called()


def test_tikz_converter_image_conversion_error(tmp_path: Path) -> None:
    """Test TikZConverter when image conversion fails."""
    tikz_dir = tmp_path / "tikz"
    tikz_dir.mkdir()
    tex_file = tikz_dir / "test.tex"
    tex_file.touch()

    directories = Mock()
    directories.tikz = tikz_dir
    directories.figures = tmp_path

    image_converter = create_autospec(ImageConverterInterface)
    latex_compiler = create_autospec(LaTeXCompilerInterface)
    file_manager = create_autospec(FileManagerInterface)
    file_manager.needs_update.return_value = True

    image_converter.convert_pdf_to_png.side_effect = ImageMagickError(
        "Conversion failed"
    )

    converter = TikZConverter(
        directories=directories,
        image_converter=image_converter,
        latex_compiler=latex_compiler,
        file_manager=file_manager,
    )

    result = converter.process_file(tex_file)
    assert not result
    assert converter.stats["failed"] == 1
    latex_compiler.compile.assert_called_once()
    image_converter.convert_pdf_to_png.assert_called_once()
