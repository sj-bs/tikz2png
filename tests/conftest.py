import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)
