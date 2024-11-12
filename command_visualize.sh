#!/bin/bash

# Define llm_models_dict
declare -A llm_models_dict=(
    ["1"]="gemini-1.5-flash-002"
    ["2"]="gemini-1.5-pro-002"
    ["3"]="gpt-4o-mini-2024-07-18"
    ["4"]="gpt-4o-2024-08-06"
    ["5"]="claude"
    ["6"]="llama_sambanova_8b"
    ["7"]="llama_sambanova_70b"
)

# Define datasets_dict
declare -A datasets_dict=(
    ["1"]='GSM8K'
    ["2"]='MultiArith'
    ["3"]='ASDiv'
    ["4"]='SVAMP'
    ["5"]='AQUA'
    ["6"]='date'
    ["7"]='p_GSM8K'
    ["8"]='GSM_Plus'
    ["9"]='GSM_IC'
    ["10"]='GSM8K_Hard'
    ["11"]='StrategyQA'
    ["12"]='commonsenseQA'
    ["13"]='wikimultihopQA'
    ["14"]='sports'
    ["15"]='reclor'
    ["16"]='CLUTRR'
    ["17"]='object_counting'
    ["18"]='navigate'
    ["19"]='causal_judgement'
    ["20"]='logical_deduction_three_objects'
    ["21"]='logical_deduction_five_objects'
    ["22"]='logical_deduction_seven_objects'
    ["23"]='reasoning_about_colored_objects'
    ["24"]='spartQA'
    ["25"]='last_letter_2'
    ["26"]='last_letter_4'
    ["27"]='coin'
    ["28"]='word_sorting'
    ["29"]='tracking_shuffled_objects_seven_objects'
    ["30"]='gpqa'
    
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

python one_step_visualize.py --dataset "$dataset" --llm_model "$llm_model" --save_html --answer_mode grounding_cot --check_correct

python one_step_visualize.py --dataset "$dataset" --llm_model "$llm_model" --save_html --answer_mode grounding_cot

