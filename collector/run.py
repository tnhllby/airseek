"""
Точка входа для запуска из корня collector/:
    python run.py
    .venv/Scripts/python run.py
"""
import sys
from pathlib import Path

# Гарантирует что collector/ есть в sys.path при любом способе запуска
sys.path.insert(0, str(Path(__file__).parent))

from app.main import main  # noqa: E402

if __name__ == "__main__":
    main()
