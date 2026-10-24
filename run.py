#!/usr/bin/env python3
import sys
from pathlib import Path

# Добавляем папку src в путь поиска модулей
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from all_to_md_desktop.main import main

if __name__ == "__main__":
    main()