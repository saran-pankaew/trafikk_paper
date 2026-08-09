from pathlib import Path
import json
import subprocess
import time
import csv
import sys
import pandas
import shutil


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]   # project/

CONFIG_FILE = PROJECT_ROOT / "config" / "Sanger-2024" / "synco.json"
WORK_DIR = SCRIPT_DIR                  # results/S2024/05_synco/

TISSUES_DIR = WORK_DIR / "tissues"
INPUT_DIR = WORK_DIR / "input"

# --------------------------------------------------
# Files that Synco needs inside input/
# Set the original locations here
# --------------------------------------------------

SYNERGY_SOURCE = INPUT_DIR / "synergy_PD.csv"
INHIBITOR_PROFILES_SOURCE = INPUT_DIR / "inhibitor_profiles.csv"
INPUT_FILES = [
    PROJECT_ROOT / "results" / "Sanger-2024" / "02_drexpa" / "drug_profiles.csv",
    SYNERGY_SOURCE,
    INHIBITOR_PROFILES_SOURCE,
]
SYNERGY_FILE = SYNERGY_SOURCE
INHIBITOR_PROFILES_FILE = INHIBITOR_PROFILES_SOURCE

OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FILE = OUTPUT_DIR / "synco_runtime_summary.csv"

ANALYSIS_MODES = [
    "cell_line",
    "inhibitor_combination",
]

def build_input_folder() -> None:
    """
    Create the Synco input directory and copy the required input files into it.
    """
    print(f"Building Synco input folder: {INPUT_DIR}")
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    for source_file in INPUT_FILES:
        source_file = source_file.resolve()
        destination = (INPUT_DIR / source_file.name).resolve()
        if source_file == destination:
            print(f"Already in input folder, skipping: {source_file.name}")
            continue
        shutil.copy2(source_file, destination)
        print(f"Copied: {source_file.name}")
        print(f"to: {destination}")

def build_config(
    template: dict,
    tissue: str,
    analysis_mode: str,
    output_dir: Path,
) -> dict:
    config = json.loads(json.dumps(template))  # deep copy

    config["paths"]["base"] = f"tissues/{tissue}/"
    config["paths"]["pipeline_runs"] = f"tissues/{tissue}/cline_output"
    config["paths"]["input"] = "input/"
    config["paths"]["output"] = (str(output_dir.relative_to(WORK_DIR)).replace("\\", "/") + "/")

    config["compare"]["analysis_mode"] = analysis_mode

    return config


def run_all_tissues() -> None:
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Missing template configuration: {CONFIG_FILE}"
        )

    build_input_folder()

    if not TISSUES_DIR.exists():
        raise FileNotFoundError(
            f"Missing tissues directory: {TISSUES_DIR}"
        )

    if not SYNERGY_FILE.exists():
        raise FileNotFoundError(
            f"Missing synergy file: {SYNERGY_FILE}"
        )

    with CONFIG_FILE.open(encoding="utf-8") as handle:
        template = json.load(handle)

    all_synergies = pandas.read_csv(SYNERGY_FILE)

    if "tissue" not in all_synergies.columns:
        raise ValueError(
            f"{SYNERGY_FILE.name} must contain a 'tissue' column"
        )

    results = []
    total_start = time.perf_counter()

    for tissue_dir in sorted(TISSUES_DIR.iterdir()):
        if not tissue_dir.is_dir():
            continue

        tissue = tissue_dir.name

        tissue_synergies = all_synergies[
            all_synergies["tissue"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
            .eq(tissue.strip().lower())
        ].copy()

        if tissue_synergies.empty:
            print(
                f"Skipping {tissue}: no synergy rows found in "
                f"{SYNERGY_FILE.name}"
            )
            continue

        temporary_synergy_file = (
            INPUT_DIR / f"_synergies_{tissue}.csv"
        )

        tissue_synergies.to_csv(
            temporary_synergy_file,
            index=False,
        )

        try:
            for analysis_mode in ANALYSIS_MODES:
                output_dir = tissue_dir / "synco_output"
                output_dir.mkdir(parents=True, exist_ok=True)

                temp_config = (
                    OUTPUT_DIR
                    / f"_synco_config_{tissue}_{analysis_mode}.json"
                )

                config = build_config(
                    template=template,
                    tissue=tissue,
                    analysis_mode=analysis_mode,
                    output_dir=output_dir,
                )

                with temp_config.open(
                    "w",
                    encoding="utf-8",
                ) as handle:
                    json.dump(config, handle, indent=2)

                command = [
                    sys.executable,
                    "-m",
                    "synco",
                    "-c",
                    str(temp_config),
                    "--synergies_filename",
                    temporary_synergy_file.name,
                ]

                print(f"\nRunning {tissue} | {analysis_mode}")
                start = time.perf_counter()

                try:
                    completed = subprocess.run(
                        command,
                        cwd=WORK_DIR,
                        check=True,
                        text=True,
                    )

                    status = "success"
                    error = ""
                    return_code = completed.returncode

                except subprocess.CalledProcessError as exc:
                    status = "failed"
                    error = str(exc)
                    return_code = exc.returncode

                finally:
                    elapsed = time.perf_counter() - start

                results.append({
                    "tissue": tissue,
                    "analysis_mode": analysis_mode,
                    "status": status,
                    "runtime_seconds": round(elapsed, 2),
                    "config": str(temp_config),
                    "synergies": str(temporary_synergy_file),
                    "return_code": return_code,
                    "error": error,
                })

                print(
                    f"{status.upper()}: {tissue} | "
                    f"{analysis_mode} in {elapsed:.2f} seconds"
                )

                temp_config.unlink(missing_ok=True)

        finally:
            temporary_synergy_file.unlink(missing_ok=True)

    total_elapsed = time.perf_counter() - total_start

    with REPORT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "tissue",
                "analysis_mode",
                "status",
                "runtime_seconds",
                "config",
                "synergies",
                "return_code",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    print("\n=== TOTAL ===")
    print(f"Runs: {len(results)}")
    print(f"Total runtime: {total_elapsed:.2f} seconds")
    print(f"Report saved to: {REPORT_FILE}")


if __name__ == "__main__":
    run_all_tissues()