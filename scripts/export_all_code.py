"""Generate docs/ALL_SOURCE_CODE.md with all project code."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FILES = [
    "main.py",
    "pyproject.toml",
    ".env.example",
    "sql/schema.sql",
    "frontend/index.html",
    "frontend/css/style.css",
    "frontend/js/app.js",
    "src/api/main.py",
    "src/api/schemas.py",
    "scripts/init_db.py",
    "scripts/run_scrapers.py",
    "scripts/run_pipeline.py",
    "scripts/run_server.py",
    "scripts/clean_data.py",
    "scripts/train_model.py",
    "scripts/generate_sample_data.py",
    "src/config.py",
    "src/database/models.py",
    "src/utils/helpers.py",
    "src/scrapers/base.py",
    "src/scrapers/sample_data.py",
    "src/scrapers/sbt_japan.py",
    "src/scrapers/carfromjapan.py",
    "src/scrapers/aaajapan.py",
    "src/scrapers/japanesecartrade.py",
    "src/scrapers/beforward.py",
    "src/etl/cleaner.py",
    "src/etl/pipeline.py",
    "src/calculator/kra_taxes.py",
    "src/calculator/import_cost.py",
    "src/ml/train.py",
    "src/ml/predict.py",
    "tests/conftest.py",
    "tests/test_calculator.py",
]

out = ROOT / "docs" / "ALL_SOURCE_CODE.md"
parts = ["# Full Source Code\n\nCopy each block into the matching file path in VS Code.\n"]

for rel in FILES:
    path = ROOT / rel
    if not path.exists():
        continue
    content = path.read_text(encoding="utf-8").rstrip()
    if rel.endswith(".py"):
        fence = "python"
    elif rel.endswith(".toml"):
        fence = "toml"
    elif rel.endswith(".js"):
        fence = "javascript"
    elif rel.endswith(".css"):
        fence = "css"
    elif rel.endswith(".html"):
        fence = "html"
    else:
        fence = "text"
    parts.append(f"\n---\n\n## `{rel}`\n\n```{fence}\n{content}\n```\n")

out.write_text("".join(parts), encoding="utf-8")
print(f"Written {out} ({out.stat().st_size:,} bytes)")
