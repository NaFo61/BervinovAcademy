#!/usr/bin/env python3
"""Собрать ZIP-архивы для импорта. Обёртка над assemble_ege_packs.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from assemble_ege_packs import build_all

if __name__ == "__main__":
    for path in build_all():
        print(path)
