"""
Repairs GNHK dataset files where .jpg and .json got swapped during
download/extraction (confirmed: some "eng_AF_001.jpg" files actually contain
JSON annotation text, while the matching "eng_AF_001.json" contains the real
JPEG bytes). Detects this by checking actual file content, not the extension,
and swaps them back. Safe to re-run -- files already correct are left alone.

Usage:
    python fix_gnhk_extensions.py <dataset_dir>
"""
import sys
from pathlib import Path

JPEG_MAGIC = b"\xff\xd8\xff"


def looks_like_jpeg(path: Path) -> bool:
    with path.open("rb") as f:
        return f.read(3) == JPEG_MAGIC


def looks_like_json_text(path: Path) -> bool:
    with path.open("rb") as f:
        head = f.read(64).lstrip()
    return head[:1] in (b"[", b"{")


def main():
    if len(sys.argv) != 2:
        print("Usage: python fix_gnhk_extensions.py <dataset_dir>")
        raise SystemExit(1)

    root = Path(sys.argv[1])
    jpg_files = {p.stem: p for p in root.rglob("*.jpg")}
    json_files = {p.stem: p for p in root.rglob("*.json")}

    fixed = 0
    already_ok = 0
    unrecognized = 0

    for stem, jpg_path in jpg_files.items():
        json_path = json_files.get(stem)
        if json_path is None:
            continue

        jpg_is_real_jpeg = looks_like_jpeg(jpg_path)
        json_is_real_jpeg = looks_like_jpeg(json_path)

        if jpg_is_real_jpeg and not json_is_real_jpeg:
            already_ok += 1
            continue

        if json_is_real_jpeg and not jpg_is_real_jpeg and looks_like_json_text(jpg_path):
            # Swap via a temp name so we never overwrite one before reading the other.
            tmp = jpg_path.with_suffix(".swap_tmp")
            jpg_path.rename(tmp)
            json_path.rename(jpg_path)
            tmp.rename(json_path)
            fixed += 1
            continue

        unrecognized += 1
        print(f"  could not confidently classify: {stem} (left untouched)")

    print(f"\nFixed (swapped back): {fixed}")
    print(f"Already correct:      {already_ok}")
    print(f"Unrecognized/skipped: {unrecognized}")


if __name__ == "__main__":
    main()
