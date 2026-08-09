from pathlib import Path
import subprocess
import time
import csv

# -------------------------
# SETTINGS
# -------------------------

tissues_dir = Path("results/Sanger-2024/run_folders")
jar_file = Path("results/Sanger-2024/03_gitsbe/gitsbe-1.3.1-jar-with-dependencies.jar")

runtime_file = Path("results/Sanger-2024/03_gitsbe/runtime_estimation/gitsbe_runtime_local.csv")

# -------------------------
# FIND CELL LINES
# -------------------------

cell_line_dirs = sorted(
    p
    for tissue_dir in tissues_dir.iterdir()
    if tissue_dir.is_dir()
    for p in tissue_dir.iterdir()
    if p.is_dir()
)

print(f"Found {len(cell_line_dirs)} cell-line directories")

# -------------------------
# CREATE RUNTIME FILE
# -------------------------

if not runtime_file.exists():
    with runtime_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "tissue",
            "cell_line",
            "runtime_seconds",
            "exit_code",
            "status"
        ])

# -------------------------
# RUN GITSBE
# -------------------------

for i, cell_line_dir in enumerate(cell_line_dirs, start=1):

    tissue = cell_line_dir.parent.name
    cell_line = cell_line_dir.name

    network_file = cell_line_dir / "cell_fate_plus.sif"
    trainingdata_file = cell_line_dir / f"{cell_line}_training"
    config_file = cell_line_dir / "config"
    modeloutputs_file = cell_line_dir / "modeloutputs"

    print()
    print("=" * 70)
    print(f"[{i}/{len(cell_line_dirs)}] {tissue} / {cell_line}")
    print("=" * 70)

    required_files = [
        network_file,
        trainingdata_file,
        config_file,
        modeloutputs_file,
    ]

    missing = [path for path in required_files if not path.exists()]

    if missing:
        print("Missing required files:")
        for path in missing:
            print(f"  {path}")

        with runtime_file.open("a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                tissue,
                cell_line,
                "",
                1,
                "missing_files"
            ])

        continue

    command = [
        r"C:\Program Files\Java\jre1.8.0_501\bin\java.exe",
        "-cp",
        str(jar_file),
        "eu.druglogics.gitsbe.Launcher",
        f"--network={network_file}",
        f"--trainingdata={trainingdata_file}",
        f"--config={config_file}",
        f"--modeloutputs={modeloutputs_file}",
    ]

    print("Starting GITSBE...")

    start = time.perf_counter()

    result = subprocess.run(command)

    runtime_seconds = time.perf_counter() - start

    if result.returncode == 0:
        status = "completed"
    else:
        status = "failed"

    print(
        f"Finished: {status} | "
        f"{runtime_seconds / 60:.2f} min | "
        f"exit code {result.returncode}"
    )

    with runtime_file.open("a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            tissue,
            cell_line,
            round(runtime_seconds, 2),
            result.returncode,
            status
        ])

print()
print("All cell lines processed.")