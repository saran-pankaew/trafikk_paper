import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]

ORIS_OUTPUT_DIR = (
    PROJECT_ROOT
    / "results"
    / "Sanger-2024"
    / "04_oris"
    / "output"
)

SYNCO_TISSUES_DIR = SCRIPT_DIR / "tissues"


def extract_all_tissues() -> None:
    if not ORIS_OUTPUT_DIR.exists():
        raise FileNotFoundError(
            f"Missing Oris output directory: {ORIS_OUTPUT_DIR}"
        )

    SYNCO_TISSUES_DIR.mkdir(parents=True, exist_ok=True)

    tissue_dirs = sorted(
        path
        for path in ORIS_OUTPUT_DIR.iterdir()
        if path.is_dir()
    )

    if not tissue_dirs:
        print(f"No tissue folders found in: {ORIS_OUTPUT_DIR}")
        return

    for tissue_dir in tissue_dirs:
        tissue = tissue_dir.name

        results_dir = (
            SYNCO_TISSUES_DIR
            / tissue
            / "cline_output"
        )
        results_dir.mkdir(parents=True, exist_ok=True)

        command = [
            sys.executable,
            "-m",
            "zipero.cli",
            "extract_results",
            "--zip_folder",
            str(tissue_dir),
            "--results_folder",
            str(results_dir),
        ]

        print(f"\nExtracting {tissue}")
        print(f"Source:      {tissue_dir}")
        print(f"Destination: {results_dir}")

        try:
            subprocess.run(
                command,
                check=True,
                text=True,
            )
            print(f"SUCCESS: {tissue}")

        except subprocess.CalledProcessError as exc:
            print(
                f"FAILED: {tissue} "
                f"(return code {exc.returncode})"
            )

    print("\nExtraction completed.")


if __name__ == "__main__":
    extract_all_tissues()