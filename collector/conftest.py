import sys
from pathlib import Path

# Добавляет collector/ в sys.path, чтобы `import app` работало из любого места
sys.path.insert(0, str(Path(__file__).parent))
