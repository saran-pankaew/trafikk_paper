from pathlib import Path
import shutil

tissues_dir = Path(r"C:\Users\viviamsb\OneDrive - NTNU\PhD Folder\Pipeline\trafikk_paper\results\Sanger-2024\05_synco\tissues")

dates_to_delete = {
    "20260721",
    "20260722",
}

dry_run = False

for tissue_dir in tissues_dir.iterdir():
    if not tissue_dir.is_dir():
        continue

    run_analysis_dir = tissue_dir / "run_analysis"

    if not run_analysis_dir.exists():
        continue

    for date in dates_to_delete:
        result_dir = run_analysis_dir / f"results_{date}"

        if result_dir.exists():
            if dry_run:
                print(f"Would delete: {result_dir}")
            else:
                shutil.rmtree(result_dir)
                print(f"Deleted: {result_dir}")