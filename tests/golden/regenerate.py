"""Regenera tests/golden/expected a partir del corpus.

Uso: uv run python -m tests.golden.regenerate
"""

from tests.golden.snapshot import EXPECTED_DIR, build_snapshots, run_pipeline, write_snapshots


def main() -> None:
    snapshots = build_snapshots(run_pipeline())
    write_snapshots(snapshots)
    print(f"{len(snapshots)} snapshots escritos en {EXPECTED_DIR}")


if __name__ == "__main__":
    main()
