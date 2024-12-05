class ImageMagickError(Exception):
    """Raised when ImageMagick operations fail.

    This exception is raised when there are issues with image conversion,
    such as missing dependencies or conversion failures.
    """

    pass


class LaTeXError(Exception):
    """Raised when LaTeX compilation fails.

    This exception is raised when there are issues with LaTeX compilation,
    such as syntax errors or missing packages.
    """

    pass
