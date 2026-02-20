#!/usr/bin/env python3
import os
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

BASELINE_FILENAME = "file_delta_baseline.log"
CHANGELOG_FILENAME = "file_delta_change.log"
EXCLUDE_FILES = {BASELINE_FILENAME, CHANGELOG_FILENAME}

# ============================================================
# UTILITIES
# ============================================================

def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def header(title: str) -> None:
    line = "=" * len(title)
    print(f"\n{title}\n{line}")

# ============================================================
# BASELINE HANDLING
# ============================================================

def load_baseline(path: Path) -> set[str]:
    if not path.exists():
        return set()
    entries = set()
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and line not in EXCLUDE_FILES:
                entries.add(line)
    return entries

def save_baseline(path: Path, files: set[str]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for file in sorted(files):
            f.write(file + "\n")

# ============================================================
# CHANGE LOGGING
# ============================================================

def append_change_log(path: Path, added: set[str], removed: set[str]) -> None:
    with path.open("a", encoding="utf-8") as log:
        log.write("\n")
        log.write(f"[RUN {timestamp()}]\n")
        if added:
            log.write("ADDED:\n")
            for item in sorted(added):
                log.write(f"+ {item}\n")
        else:
            log.write("ADDED: (none)\n")
        if removed:
            log.write("REMOVED:\n")
            for item in sorted(removed):
                log.write(f"- {item}\n")
        else:
            log.write("REMOVED: (none)\n")

# ============================================================
# SCANNING
# ============================================================

def scan_files(root: Path) -> set[str]:
    results = set()
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name not in EXCLUDE_FILES:
                results.add(os.path.join(dirpath, name))
    return results

# ============================================================
# DELTA ENGINE
# ============================================================

class DeltaScanner:
    def __init__(self, root: Path):
        self.root = root
        self.baseline_path = root / BASELINE_FILENAME
        self.change_log_path = root / CHANGELOG_FILENAME

    def run(self) -> None:
        previous = load_baseline(self.baseline_path)
        current = scan_files(self.root)

        added = current - previous
        removed = previous - current

        self.render_results(added, removed, current)
        append_change_log(self.change_log_path, added, removed)
        save_baseline(self.baseline_path, current)

        # Final summary report
        self.print_summary(added, removed, current)

        input("\nPress ENTER to exit and review logs...")

    @staticmethod
    def render_results(added: set[str], removed: set[str], seen: set[str]) -> None:
        header("ADDED FILES")
        print("\n".join(sorted(added)) if added else "(none)")

        header("REMOVED FILES")
        print("\n".join(sorted(removed)) if removed else "(none)")

        header("SEEN FILES")
        for path in sorted(seen):
            if path not in added and path not in removed:
                print(f"* {path}")

    @staticmethod
    def print_summary(added: set[str], removed: set[str], seen: set[str]) -> None:
        header("SCAN SUMMARY")
        print(f"Timestamp : {timestamp()}")
        print(f"Root Path : {Path.cwd()}")
        print(f"Added     : {len(added)} file(s)")
        print(f"Removed   : {len(removed)} file(s)")
        print(f"Seen      : {len(seen) - len(added) - len(removed)} file(s)")
        print("=" * 30)
        print(f"Baseline saved at : {Path.cwd() / BASELINE_FILENAME}")
        print(f"Changes logged at : {Path.cwd() / CHANGELOG_FILENAME}")
        print("=" * 30)
        print("Scan complete. Review results above.")

# ============================================================
# MAIN
# ============================================================

def main():
    try:
        root = Path(__file__).resolve().parent
    except NameError:
        root = Path.cwd()

    scanner = DeltaScanner(root)
    scanner.run()

if __name__ == "__main__":
    main()
