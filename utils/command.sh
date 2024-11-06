#!/bin/bash

# Define llm_models_dict
declare -A llm_models_dict=(
    ["1"]="gemini-1.5-flash-002"
    ["2"]="gemini-1.5-pro-002"
    ["3"]="gpt-4o-mini-2024-07-18"
    ["4"]="gpt-4o-2024-08-06"
    ["5"]="claude"
)

# Define datasets_dict
declare -A datasets_dict=(
    ["1"]='GSM8K'
    ["2"]='StrategyQA'
    ["3"]='p_GSM8K'
    ["4"]='AQUA'
    ["5"]='MultiArith'
    ["6"]='ASDiv'
    ["7"]='SVAMP'
    ["8"]='commonsenseQA'
    ["9"]='wikimultihopQA'
    ["10"]='date'
    ["11"]='sports'
    ["12"]='reclor'
    ["13"]='CLUTRR'
    ["14"]='object_counting'
    ["15"]='navigate'
    ["16"]='causal_judgement'
    ["17"]='logical_deduction_three_objects'
    ["18"]='logical_deduction_five_objects'
    ["19"]='logical_deduction_seven_objects'
    ["20"]='reasoning_about_colored_objects'
    ["21"]='GSM_Plus'
    ["22"]='GSM_IC'
    ["23"]='spartQA'
    ["24"]='last_letter_2'
    ["25"]='last_letter_4'
    ["26"]='coin'
    ["27"]='word_sorting'
    ["28"]='tracking_shuffled_objects_seven_objects'
    ["29"]='gpqa'
    ["30"]='GSM8K_Hard'
)

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

# Print the combination being run for logging purposes
# echo "Running eval_da_and_cot.py for model: $llm_model and dataset: $dataset"

python eval_da_and_cot.py --llm_model "$llm_model" --data_mode longest --answer_mode cot --dataset "$dataset"
python eval_da_and_cot.py --llm_model "$llm_model" --data_mode longest --answer_mode grounding_cot --dataset "$dataset"

# python eval_mmlu.py --llm_model "$llm_model" --data_mode longest --answer_mode cot --dataset "$dataset"
# python eval_mmlu.py --llm_model "$llm_model" --data_mode longest --answer_mode grounding_cot --dataset "$dataset"

# echo "Running eval_gcot.py for model: $llm_model and dataset: $dataset"
# python eval_gcot.py --llm_model "$llm_model" --data_mode longest --dataset "$dataset"