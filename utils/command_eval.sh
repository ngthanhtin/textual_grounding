#!/bin/bash

source ../configs/llm_and_datasets_mapping.sh

# Check if two arguments are passed (model key and dataset key)
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <model_key> <dataset_key>"
    echo "Example: $0 1 24 (to run llm_model[1] and dataset[24])"
    exit 1
fi

# Get model_key and dataset_key from input
model_key=$1
dataset_key=$2

# Validate if the provided keys exist in the dictionaries
if [[ -z "${llm_models_dict[$model_key]}" ]]; then
    echo "Error: Invalid llm_model key: $model_key"
    exit 1
fi

if [[ -z "${datasets_dict[$dataset_key]}" ]]; then
    echo "Error: Invalid dataset key: $dataset_key"
    exit 1
fi

# Extract the specific llm_model and dataset
llm_model="${llm_models_dict[$model_key]}"
dataset="${datasets_dict[$dataset_key]}"

echo "Running for model: $llm_model and dataset: $dataset and run_mode: cot" 
python evaluate.py --llm_model "$llm_model" --data_mode longest --answer_mode cot --dataset "$dataset"
echo "Running for model: $llm_model and dataset: $dataset and run_mode: grounding_cot" 
python evaluate.py --llm_model "$llm_model" --data_mode longest --answer_mode grounding_cot --dataset "$dataset"

