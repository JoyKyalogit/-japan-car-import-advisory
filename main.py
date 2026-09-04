"""CLI entry point for Japan Car Import Advisory Platform."""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Japan Car Import Advisory Platform")
    parser.add_argument(
        "command",
        choices=["init", "scrape", "clean", "train", "server", "all"],
        help="Command to run",
    )
    args = parser.parse_args()
    root = Path(__file__).parent
    py = sys.executable

    commands = {
        "init": [py, str(root / "scripts" / "init_db.py")],
        "scrape": [py, str(root / "scripts" / "run_scrapers.py")],
        "clean": [py, str(root / "scripts" / "clean_data.py")],
        "train": [py, str(root / "scripts" / "train_model.py")],
        "server": [py, str(root / "scripts" / "run_server.py")],
    }

    if args.command == "all":
        for cmd in ["init", "scrape", "train"]:
            print(f"\n{'='*50}\nRunning: {cmd}\n{'='*50}")
            subprocess.run(commands[cmd], check=True)
        print("\nStarting web server...")
        subprocess.run(commands["server"])
    else:
        subprocess.run(commands[args.command])


if __name__ == "__main__":
    main()
