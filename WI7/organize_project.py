"""
One-time cleanup for the WI2 project folder. Safe to re-run (skips anything
already done, and retries anything that failed last time). Run this from
inside the WI2 folder.

What it does, and why:
  - Deletes __pycache__          (auto-regenerated junk, never needed on disk)
  - Deletes benchmark-images-gnhk (an early hand-picked subset of GNHK images,
                                    now fully superseded by dataset/GNHK-dataset-main/test)
  - Deletes ocr_benchmark.csv     (the default-named log file ended up mixing
                                    leftover rows from the very first smoke test
                                    with a partial later run -- not reliable data.
                                    The real, complete per-engine results are the
                                    other three CSVs, which this script keeps.)
  - Moves the three real result CSVs into a new results/ folder

Windows note: if this project folder lives inside OneDrive (or Dropbox/Google
Drive), the sync client can briefly lock a file/folder right after it's
touched, which surfaces as "PermissionError: Access is denied" even though
nothing is actually wrong. This script clears read-only flags and retries a
few times with a short pause to ride that out, and -- importantly -- one
step failing no longer stops the rest of the cleanup from running.

Usage:
    python organize_project.py
"""
import shutil
import stat
import time
from pathlib import Path

ROOT = Path(__file__).parent
RETRIES = 5
RETRY_DELAY_SECONDS = 2


def _clear_readonly(path: Path):
    """Recursively clear the read-only flag -- the other common Windows cause
    of PermissionError on rmtree, separate from the OneDrive-lock issue."""
    if path.is_dir():
        for child in path.rglob("*"):
            try:
                child.chmod(child.stat().st_mode | stat.S_IWRITE)
            except OSError:
                pass
    try:
        path.chmod(path.stat().st_mode | stat.S_IWRITE)
    except OSError:
        pass


def remove_dir(path: Path, reason: str):
    if not path.exists():
        print(f"skip (not found): {path.name}")
        return

    _clear_readonly(path)
    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            shutil.rmtree(path)
            print(f"removed dir:  {path.name}  ({reason})")
            return
        except PermissionError as exc:
            last_error = exc
            if attempt < RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    print(
        f"COULD NOT remove {path.name}: {last_error}\n"
        f"  Likely a sync-client lock (OneDrive/Dropbox) or the folder is open "
        f"in Explorer/another program. Close any window showing that folder, "
        f"wait a few seconds, and re-run this script -- everything else below "
        f"still ran."
    )


def remove_file(path: Path, reason: str):
    if not path.exists():
        print(f"skip (not found): {path.name}")
        return

    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            path.chmod(path.stat().st_mode | stat.S_IWRITE)
            path.unlink()
            print(f"removed file: {path.name}  ({reason})")
            return
        except PermissionError as exc:
            last_error = exc
            if attempt < RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    print(f"COULD NOT remove {path.name}: {last_error} -- re-run this script later to retry.")


def main():
    remove_dir(ROOT / "__pycache__", "auto-regenerated, not needed on disk")
    remove_dir(
        ROOT / "benchmark-images-gnhk",
        "superseded by dataset/GNHK-dataset-main/test",
    )
    remove_file(
        ROOT / "ocr_benchmark.csv",
        "mixed leftover rows from an old smoke test + a partial run, not reliable",
    )

    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    for name in (
        "ocr_benchmark_trocr_100.csv",
        "ocr_benchmark_rapidocr_100.csv",
        "ocr_benchmark_paddle_100.csv",
    ):
        src = ROOT / name
        if not src.exists():
            print(f"skip (not found): {name}")
            continue
        try:
            shutil.move(str(src), str(results_dir / name))
            print(f"moved to results/: {name}")
        except PermissionError as exc:
            print(f"COULD NOT move {name}: {exc} -- re-run this script later to retry.")

    print("\nDone (see any COULD NOT lines above for anything that needs a re-run).")
    print("Final layout should be:")
    print("  bench.py, fix_gnhk_extensions.py, README.md")
    print("  dataset/, models/, results/")
    print("  .venv/, .venv-paddle/, .venv-rapidocr/")
    print(
        "\nNote: .venv-paddle is only needed if you still want to re-run the "
        "PaddleOCR comparison -- otherwise it's safe to delete manually to save "
        "disk space, since bench.py no longer uses it."
    )


if __name__ == "__main__":
    main()
