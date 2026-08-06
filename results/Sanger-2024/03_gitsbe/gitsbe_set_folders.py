from pathlib import Path
import shutil


def copy_files_to_cell_line_folders(
    tissues_directory: str | Path,
    drug_panel_file: str | Path,
    network_file: str | Path,
    config_file: str | Path,
    model_outputs: str | Path
) -> None:
    tissues_directory = Path(tissues_directory)

    files_to_copy = [
        Path(drug_panel_file),
        Path(network_file),
        Path(config_file),
        Path(model_outputs),
    ]

    missing_files = [file for file in files_to_copy if not file.is_file()]
    if missing_files:
        raise FileNotFoundError(f"Missing files: {missing_files}")

    for tissue_folder in sorted(tissues_directory.iterdir()):
        if not tissue_folder.is_dir():
            continue

        for cell_line_folder in sorted(tissue_folder.iterdir()):
            if not cell_line_folder.is_dir():
                continue

            for source_file in files_to_copy:
                destination_name = (
                    "config"
                    if source_file == Path(config_file)
                    else source_file.name
                )

                shutil.copy2(
                    source_file,
                    cell_line_folder / destination_name,
                )

            print(f"Copied files to: {tissue_folder.name}/{cell_line_folder.name}")


copy_files_to_cell_line_folders(
    tissues_directory="results/Sanger-2024/run_folders",
    drug_panel_file="results/Sanger-2024/02_drexpa/drugpanel",
    network_file="data/network/cell_fate_plus.sif",
    config_file="config/Sanger-2024/gitsbe_config",
    model_outputs="data/network/modeloutputs"
)
