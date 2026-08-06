#!/bin/bash
#SBATCH --job-name=gitsbe_tissues  # Name of the job
#SBATCH --output=logs/gitsbe_%A_%a.out
#SBATCH --error=logs/gitsbe_%A_%a.err
#SBATCH --array=0-1                   # Array range (adjust based on your directories)
#SBATCH --cpus-per-task=10               # Number of cores per job
#SBATCH --mem=10G                        # Memory per job
#SBATCH --time=04:00:00                 # Time limit for each job
#SBATCH --partition=CPUQ             # Partition to submit to

set -u 
module load  Java/11.0.20

# Directory containing the tissue folders.
# Submit the job from the directory containing this folder,
# or replace this with an absolute path.
tissues_dir="run_folders"

jar_file="gitsbe-1.3.1-jar-with-dependencies.jar"
runtime_dir="runtime_logs"
mkdir -p logs runtime_logs

# Find every cell-line directory nested one level below each tissue.
mapfile -t cell_line_dirs < <(
    find "$tissues_dir" \
        -mindepth 2 \
        -maxdepth 2 \
        -type d \
        | sort
)

number_of_cell_lines=${#cell_line_dirs[@]}

echo "Total cell-line directories detected: $number_of_cell_lines"
echo "SLURM array task ID: $SLURM_ARRAY_TASK_ID"

# Protect against an array range larger than the number of cell lines.
if (( SLURM_ARRAY_TASK_ID >= number_of_cell_lines )); then
    echo "No cell line assigned to array task $SLURM_ARRAY_TASK_ID"
    exit 0
fi

cell_line_dir="${cell_line_dirs[$SLURM_ARRAY_TASK_ID]}"
cell_line=$(basename "$cell_line_dir")
tissue=$(basename "$(dirname "$cell_line_dir")")

network_file="${cell_line_dir}/cell_fate_plus.sif"
trainingdata_file="${cell_line_dir}/${cell_line}_training"
config_file="${cell_line_dir}/config"
modeloutputs_file="${cell_line_dir}/modeloutputs"

echo "Tissue: $tissue"
echo "Cell line: $cell_line"
echo "Cell-line directory: $cell_line_dir"

echo "Checking files:"
echo "Network: $network_file"
echo "Training data: $trainingdata_file"
echo "Config: $config_file"
echo "Model outputs: $modeloutputs_file"

missing_files=0

for required_file in \
    "$network_file" \
    "$trainingdata_file" \
    "$config_file" \
    "$modeloutputs_file"
do
    if [[ ! -f "$required_file" ]]; then
        echo "Missing file: $required_file" >&2
        missing_files=1
    fi
done

runtime_file="${runtime_dir}/${tissue}_${cell_line}_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}.csv"

if (( missing_files != 0 )); then
    echo "GITSBE skipped because required files are missing." >&2

    echo \
"job_id,array_task_id,tissue,cell_line,start_time,end_time,runtime_seconds,exit_code,status" \
        > "$runtime_file"

    echo \
"${SLURM_JOB_ID},${SLURM_ARRAY_TASK_ID},${tissue},${cell_line},,,,1,missing_files" \
        >> "$runtime_file"

    exit 1
fi

start_timestamp=$(date --iso-8601=seconds)
start_seconds=$(date +%s)

echo "GITSBE started at: $start_timestamp"

java -cp "$jar_file" eu.druglogics.gitsbe.Launcher \
    --network="$network_file" \
    --trainingdata="$trainingdata_file" \
    --config="$config_file" \
    --modeloutputs="$modeloutputs_file"

exit_code=$?

end_seconds=$(date +%s)
end_timestamp=$(date --iso-8601=seconds)
runtime_seconds=$((end_seconds - start_seconds))

if (( exit_code == 0 )); then
    status="completed"
else
    status="failed"
fi

echo "GITSBE finished at: $end_timestamp"
echo "Runtime: $runtime_seconds seconds"
echo "Exit code: $exit_code"
echo "Status: $status"

echo \
"job_id,array_task_id,tissue,cell_line,start_time,end_time,runtime_seconds,exit_code,status" \
    > "$runtime_file"

echo \
"${SLURM_JOB_ID},${SLURM_ARRAY_TASK_ID},${tissue},${cell_line},${start_timestamp},${end_timestamp},${runtime_seconds},${exit_code},${status}" \
    >> "$runtime_file"

exit "$exit_code"