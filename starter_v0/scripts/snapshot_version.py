"""Save a copy of the current prompt + tools under artifacts/snapshots/<version>/.

The run JSON only stores hashes, so without a snapshot the text of an old
version is lost once the file is edited. The dashboard matches snapshots to
runs by hash, so it can show the code diff between any two versions.

Usage (run right after you finish editing a version, before the next edit):
  python scripts/snapshot_version.py v3
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
FILES = ("system_prompt.md", "tools.yaml")


def short(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("version", help="version label, e.g. v3")
    parser.add_argument("--force", action="store_true", help="overwrite an existing snapshot")
    parser.add_argument("--owner", default=None, help="optional sub-folder, e.g. 2A202603687-BuiAnhDung -> snapshots/<owner>/<version>")
    args = parser.parse_args()

    base = ARTIFACTS / "snapshots" / args.owner if args.owner else ARTIFACTS / "snapshots"
    target = base / args.version
    if target.exists() and not args.force:
        raise SystemExit(f"{target} already exists. Use --force to overwrite.")
    target.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copyfile(ARTIFACTS / name, target / name)
        print(f"{name}: hash {short(target / name)}")
    print(f"Saved snapshot to {target}")


if __name__ == "__main__":
    main()
