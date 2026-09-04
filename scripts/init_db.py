"""Initialize the database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.models import init_db


def main():
    engine = init_db()
    print(f"Database initialized: {engine.url}")


if __name__ == "__main__":
    main()
