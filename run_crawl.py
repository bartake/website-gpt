"""Run the My Company site crawler. Output: data/pages.jsonl"""
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CRAWLER_DIR = PROJECT_ROOT / "crawler"
DATA_DIR = PROJECT_ROOT / "data"


def main():
    DATA_DIR.mkdir(exist_ok=True)
    result = subprocess.run(
        [sys.executable, "-m", "scrapy", "crawl", "my_company"],
        cwd=str(CRAWLER_DIR),
    )
    return result.returncode


if __name__ == "__main__":
    exit(main())
