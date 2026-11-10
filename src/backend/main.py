"""Entry point: `uvicorn src.backend.main:app` (run from the repository root)."""

import logging

from .app import create_app
from .config import load_settings


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = create_app(load_settings())
