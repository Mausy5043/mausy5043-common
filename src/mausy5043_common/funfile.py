#!/usr/bin/env python3

# mausy5043-common
# Copyright (C) 2025  Maurice (mausy5043) Hendrix
# AGPL-3.0-or-later  - see LICENSE

"""Provide file operation functions."""

import logging
from pathlib import Path

LOGGER: logging.Logger = logging.getLogger(__name__)


def cat(file_name: str) -> str:
    """Read a file (line-by-line) into a variable.

    Args:
        file_name (str) : file to read from

    Returns:
          (str) : file contents
    """
    contents: str = ""
    try:
        file_path = Path(file_name)
        if file_path.is_file():
            contents = file_path.read_text(encoding="utf-8")
    except Exception as her:
        LOGGER.error(f"Accessing {file_name} returned: {her}")
    return contents
