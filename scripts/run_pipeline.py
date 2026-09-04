"""Run the full data pipeline: init → scrape → train."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def main():
    steps = [
        ("init_db.py", "Initializing database"),
        ("run_scrapers.py", "Scraping / generating data"),
        ("train_model.py", "Training ML model"),
    ]
    for script, label in steps:
        print(f"\n{'=' * 50}\n{label}\n{'=' * 50}")
        subprocess.run([PY, str(ROOT / "scripts" / script)], check=True)
    print("\nPipeline complete. Launch dashboard with:")
    print("  uv run python scripts/run_server.py")


if __name__ == "__main__":
    main()
