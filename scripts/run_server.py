"""Run the FastAPI web server."""

import os
import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if __name__ == "__main__":
    # Local default binds to localhost; cloud hosts set HOST=0.0.0.0
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8003"))
    reload = os.environ.get("RELOAD", "true").lower() in {"1", "true", "yes"}
    print("\n  Japan Car Import Advisory — Web Server")
    print(f"  Open in your browser: http://{host}:{port}")
    print("  Keep this terminal open while using the app.\n")
    uvicorn.run("src.api.main:app", host=host, port=port, reload=reload)
