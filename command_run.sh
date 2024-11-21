#!/bin/bash

source ./configs/llm_and_datasets_mapping.sh

# Define run modes
declare -A run_modes_dict=(
    ["1"]="cot"
    ["2"]="grounding_cot"
)

# Check if two arguments are passed (model key and dataset key)
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <model_key> <dataset_key> <run_mode_key>"
    echo "Example: $0 2 1 1 (to run llm_model[1] and dataset[24]) with run_mode[1]"
    exit 1
fi

# Get model_key and dataset_key from input
model_key=$1
dataset_key=$2
run_mode_key=$3

# Validate if the provided keys exist in the dictionaries
if [[ -z "${llm_models_dict[$model_key]}" ]]; then
    echo "Error: Invalid llm_model key: $model_key"
    exit 1
fi

if [[ -z "${datasets_dict[$dataset_key]}" ]]; then
    echo "Error: Invalid dataset key: $dataset_key"
    exit 1
fi

if [[ -z "${run_modes_dict[$run_mode_key]}" ]]; then
    echo "Error: Invalid run mode key: $run_mode_key"
    exit 1
fi

# Extract the specific llm_model and dataset
llm_model="${llm_models_dict[$model_key]}"
dataset="${datasets_dict[$dataset_key]}"
run_mode="${run_modes_dict[$run_mode_key]}"

echo "Running for model: $llm_model and dataset: $dataset" and run_mode: $run_mode

python one_step_grounding.py --prompt_used fs_inst --save_answer --llm_model "$llm_model" --dataset "$dataset" --answer_mode "$run_mode" --data_mode longest