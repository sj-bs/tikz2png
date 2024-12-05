import logging
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn
from rich.text import Text

from .config import Config, create_argument_parser
from .directories import Directories
from .errors import ImageMagickError, LaTeXError
from .interfaces import (
    FileManagerInterface,
    ImageConverterInterface,
    LaTeXCompilerInterface,
)

__all__ = [
    "TikZConverter",
    "Directories",
    "ImageConverter",
    "LaTeXCompiler",
    "FileManager",
]

console = Console()
logger = logging.getLogger("tikz2png")


class ImageConverter(ImageConverterInterface):
    """Handles conversion of PDF files to PNG format using ImageMagick."""

    def __init__(self) -> None:
        self.command: str = self._get_imagemagick_command()

    def _get_imagemagick_command(self) -> str:
        """Determine which ImageMagick command to utilise."""
        if platform.system() == "Windows":
            # On Windows, assume magick.exe
            if shutil.which("magick.exe"):
                return "magick.exe"
        else:
            magick_path = shutil.which("magick")
            if magick_path:
                return "magick"
            convert_path = shutil.which("convert")
            if convert_path:
                logger.warning(
                    "Using deprecated 'convert' command. Consider updating ImageMagick."
                )
                return "convert"
        raise ImageMagickError("ImageMagick not found. Please install ImageMagick.")

    def convert_pdf_to_png(self, pdf_file: Path, png_path: Path) -> None:
        try:
            subprocess.run(
                [
                    self.command,
                    "-density",
                    "300",
                    str(pdf_file),
                    "-quality",
                    "100",
                    str(png_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as err:
            raise ImageMagickError(f"Image conversion failed: {err.stderr}") from err


class LaTeXCompiler(LaTeXCompilerInterface):
    """Handles compilation of LaTeX files to PDF format."""

    def __init__(self) -> None:
        self.latex_command = self._get_latex_command()

    def _get_latex_command(self) -> str:
        """Get the appropriate LaTeX command for current OS."""
        if platform.system() == "Windows":
            candidates = ["pdflatex.exe", "latex.exe"]
        else:
            candidates = ["pdflatex", "latex"]

        for cmd in candidates:
            if shutil.which(cmd):
                return cmd
        raise LaTeXError("LaTeX compiler not found. Please install LaTeX.")

    def compile(self, tex_file: Path) -> None:
        """
        Compile LaTeX file to PDF.

        Args:
            tex_file: Path to the LaTeX file to compile

        Raises:
            LaTeXError: If compilation fails
            FileNotFoundError: If tex_file doesn't exist
        """
        if not tex_file.exists():
            raise FileNotFoundError(f"LaTeX file not found: {tex_file}")

        working_dir = tex_file.parent
        tex_filename = tex_file.name

        try:
            subprocess.run(
                [self.latex_command, "-interaction=nonstopmode", tex_filename],
                capture_output=True,
                text=True,
                check=True,
                cwd=working_dir,
            )
        except subprocess.CalledProcessError as err:
            raise LaTeXError(
                f"LaTeX compilation failed: {extract_latex_errors(err.stderr)}"
            ) from err


class FileManager(FileManagerInterface):
    """Handles file operations and status checks."""

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialise FileManager with a console for output."""
        self.console = console or Console()

    def needs_update(self, tex_file: Path, png_file: Path) -> bool:
        """Check if PNG needs to be regenerated based on file timestamps."""
        if not png_file.exists():
            self.console.print(f"🆕 [cyan]Will generate:[/] {png_file.name}")
            return True
        is_newer = tex_file.stat().st_mtime > png_file.stat().st_mtime
        if not is_newer:
            self.console.print(
                f"\n⏭️  [yellow]Skipping:[/] {tex_file.name} (PNG is up to date)"
            )
        return is_newer

    def cleanup_auxiliary_files(self, base_path: Path) -> None:
        """Clean up auxiliary files using the full path."""
        working_dir = base_path.parent
        base_name = base_path.stem
        for ext in [".aux", ".log", ".pdf", ".pdb_latexmk", ".fls"]:
            aux_file = working_dir / f"{base_name}{ext}"
            try:
                if aux_file.exists():
                    aux_file.unlink()
                    self.console.print(
                        f"\n🗑️  [dim]Removed auxiliary file:[/] {aux_file.name}"
                    )
            except Exception as err:
                self.console.print(
                    f"\n⚠️  [yellow]Failed to remove[/] {aux_file.name}: {str(err)}"
                )


def extract_latex_errors(stderr: str) -> str:
    """Extract relevant error messages from LaTeX output.

    Args:
        stderr: The standard error output from LaTeX compilation

    Returns:
        str: Formatted error messages or the original stderr if no specific errors found
    """
    error_lines: List[str] = []
    for line in stderr.splitlines():
        if any(x in line.lower() for x in ["error", "!", "fatal"]):
            error_lines.append(line.strip())
    return "\n".join(error_lines) if error_lines else stderr


class TikZConverter:
    """Main converter class that orchestrates the TikZ to PNG conversion process.

    This class coordinates the conversion process by managing file operations,
    LaTeX compilation, and image conversion.

    Attributes:
        directories: Project directory configuration
        image_converter: Component for PDF to PNG conversion
        latex_compiler: Component for LaTeX compilation
        file_manager: Component for file operations
        stats: Dictionary tracking conversion statistics
    """

    def __init__(
        self,
        directories: Directories,
        image_converter: ImageConverterInterface,
        latex_compiler: LaTeXCompilerInterface,
        file_manager: FileManagerInterface,
    ) -> None:
        self.directories = directories
        self.image_converter = image_converter
        self.latex_compiler = latex_compiler
        self.file_manager = file_manager
        self.stats = {"processed": 0, "skipped": 0, "failed": 0}

    def process_file(
        self,
        tex_file: Path,
        force: bool = False,
        task_id: Optional[TaskID] = None,
        progress: Optional[Progress] = None,
    ) -> bool:
        png_path: Path = self.directories.figures / f"{tex_file.stem}.png"
        if not force and not self.file_manager.needs_update(tex_file, png_path):
            self.stats["skipped"] += 1
            return False

        try:
            if progress and task_id is not None:
                progress.update(task_id, description=f"Processing {tex_file.name}")

            self.latex_compiler.compile(tex_file)
            pdf_file = (tex_file.parent / f"{tex_file.stem}.pdf").absolute()
            self.image_converter.convert_pdf_to_png(pdf_file, png_path)
            self.file_manager.cleanup_auxiliary_files(tex_file.absolute())

            self.stats["processed"] += 1
            return True
        except Exception as e:
            self.stats["failed"] += 1
            if progress:
                progress.console.print(
                    f"[red]Error processing {tex_file.name}: {str(e)}[/]"
                )
            return False

    def run(self, force: bool = False) -> None:
        tex_files: Sequence[Path] = list(self.directories.tikz.glob("*.tex"))
        if not tex_files:
            logger.warning("No .tex files found in Assets/TikZ!")
            return

        console.print(
            Panel(
                f"🔍 Found [cyan]{len(tex_files)}[/] TikZ files to process",
                width=100,
                padding=(1, 2),
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Processing files...", total=len(tex_files))

            for tex_file in tex_files:
                if self.process_file(tex_file, force, task, progress):
                    logger.info(f"✅ [green]Processed:[/] {tex_file.name}")
                progress.advance(task)

        summary = Text()
        summary.append("\n📊 Summary:\n", style="bold")
        summary.append(f"✅ Processed: {self.stats['processed']}\n", style="green")
        summary.append(f"⏭️  Skipped: {self.stats['skipped']}\n", style="yellow")
        summary.append(f"❌ Failed: {self.stats['failed']}\n", style="red")
        console.print(Panel(summary, width=100, padding=(1, 2)))


def create_converter(config: "Config") -> "TikZConverter":
    """Create a new TikZConverter instance with the given configuration.

    Args:
        config (Config): The configuration object containing tikz_dir and output_dir
        settings

    Returns:
        TikZConverter: A configured TikZConverter instance
    """
    directories: Directories = Directories.create(
        tikz_path=config.tikz_dir, figures_path=config.output_dir
    )
    directories.validate()

    return TikZConverter(
        directories=directories,
        image_converter=ImageConverter(),
        latex_compiler=LaTeXCompiler(),
        file_manager=FileManager(console=console),
    )


def main() -> None:
    """Main execution function."""
    parser = create_argument_parser()
    args = parser.parse_args()
    config = Config.from_args(args)

    if config.quiet:
        logging.getLogger("tikz2png").setLevel(logging.WARNING)

    try:
        console.print("[bold green]🚀 Initialising converter...[/]")
        converter = create_converter(config)
        converter.run(config.force)
    except Exception as e:
        console.print(f"[red bold]❌ Error:[/] {str(e)}")
        sys.exit(1)


if sys.version_info < (3, 9):
    raise RuntimeError("tikz2png requires Python 3.9 or higher")

if __name__ == "__main__":
    main()
