from abc import ABC, abstractmethod
from pathlib import Path


class ImageConverterInterface(ABC):
    """Interface for converting PDF files to PNG format."""

    @abstractmethod
    def convert_pdf_to_png(
        self, pdf_file: Path, png_path: Path
    ) -> None:  # pragma: no cover
        """Convert a PDF file to PNG format.

        Args:
            pdf_file: Path to the source PDF file
            png_path: Path where the PNG should be saved
        """
        pass


class LaTeXCompilerInterface(ABC):
    """Interface for compiling LaTeX documents."""

    @abstractmethod
    def compile(self, tex_file: Path) -> None:  # pragma: no cover
        """Compile a LaTeX file to PDF.

        Args:
            tex_file: Path to the LaTeX file to compile
        """
        pass


class FileManagerInterface(ABC):
    """Interface for managing file operations during conversion."""

    @abstractmethod
    def needs_update(self, tex_file: Path, png_file: Path) -> bool:  # pragma: no cover
        """Check if PNG needs to be regenerated based on file timestamps.

        Args:
            tex_file: Path to the source TeX file
            png_file: Path to the target PNG file

        Returns:
            bool: True if PNG needs updating, False otherwise
        """
        pass

    @abstractmethod
    def cleanup_auxiliary_files(self, base_path: Path) -> None:  # pragma: no cover
        """Clean up auxiliary files generated during conversion.

        Args:
            base_path: Base path where auxiliary files are located
        """
        pass
