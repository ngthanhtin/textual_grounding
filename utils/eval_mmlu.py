"""Response Parsing and Evaluation for various models"""
from typing import Dict

import sys, os, re, random, yaml
sys.path.insert(0, '../')
random.seed(42)
import numpy as np
import pandas as pd

from arg_parser import get_common_args
from utils import retrieve_gts

from mmlu import parse_open_response, parse_multi_choice_response, parse_options, check_math_answer

from utils import read_jsonl_file

def extract_options_to_dict(text):
    # Regular expression to match the pattern of options
    pattern = r"\(([A-F])\)\s+(.+)"
    
    # Find all matches in the text
    matches = re.findall(pattern, text)
    
    # Initialize a dictionary to store the options
    options_dict = {}
    
    # Loop through matches and populate the dictionary
    for label, description in matches:
        options_dict[label] = description.strip()

    return options_dict

def compute_acc(questions, answers, gts, dataset):

    # Append each question and its highlighted answer to the HTML content
    total_acc = 0
    failed_follow_format_question = 0
    failed_follow_format_final_answer = 0

    for i, (question, answer, gt) in enumerate(zip(questions, answers, gts)):
        if dataset in ['GSM8K', 'p_GSM8K', 'MultiArith', 'SVAMP', 'ASDiv', 'GSM8K_Hard', 'GSM_Plus']:
            total_acc += check_math_answer(answer, gt)
            
        elif dataset in ['AQUA']:
            index2ans = parse_options(question)
            # remove ' in index2ans
            index2ans = {key: value.replace("'", "") for key, value in index2ans.items()}
            
            # all_choices = list(index2ans.keys())
            # pred_index = parse_multi_choice_response(answer, all_choices, index2ans)
            
            gt_number  = index2ans[gt]
            
            try:
                extracted_answer = answer.split('{')[-1].split('}')[0]
                if gt.upper() in extracted_answer or gt_number in extracted_answer:
                    total_acc += 1
                    # print('Answer: ', answer[-200:], 'GT: ', gt, gt_number)
                    # print('------------------------------------')
            except:
                
                if 'The closest answer option is' in answer:
                    extracted_answer = answer.split('The closest answer option is')[-1]
                elif'The correct answer is' in answer:
                    extracted_answer = answer.split('The correct answer is')[-1]
                elif 'Therefore, the answer is' in answer:
                    extracted_answer = answer.split('Therefore, the answer is')[-1]
                elif 'Therefore the answer is' in answer:
                    extracted_answer = answer.split('Therefore the answer is')[-1]
                else:
                    extracted_answer = answer[-200:]
                # if gt.upper() == label or gt_number in extracted_answer:
                #     total_acc += 1
                # else:
                pattern = r"(?i)([A-G])\)?[\s-]*\{?([^\{\}\(\)]+?)\}?(?=\s*[\(\{\[]?[A-G]\)?]|$)"
                matches = re.findall(pattern, extracted_answer)

                # Loop through matches and format them
                for label, extracted_answer in matches:
                    if gt.upper() == label or gt_number in extracted_answer:
                        total_acc += 1
                        # print('Answer: ', answer[-200:], 'GT: ', gt, gt_number)
                        # print('------------------------------------')
                    else:
                        print('Answer: ', answer[-200:], 'GT: ', gt, gt_number)
                        print('------------------------------------')

        elif dataset in ['logical_deduction_seven_objects', 'reasoning_about_colored_objects']:
            options_dict = extract_options_to_dict(question)

            if 'Answer: ' in answer:
                answer = answer.split('Answer: ')[-1].strip()
            
            if len(answer) < 10: # Sometimes it answers the option directly.
                if gt in answer:
                    total_acc += 1
                    continue
                
            extracted_answer = answer.split('{')[-1].split('}')[0]    
            if extracted_answer == answer: # can not extract
                extracted_answer = answer.split('(')[-1].split(')')[0]
                if extracted_answer == answer: # can not extract  
                    if 'The closest answer option is' in answer:
                        extracted_answer = answer.split('The closest answer option is')[-1]
                    elif'The correct answer is' in answer:
                        extracted_answer = answer.split('The correct answer is')[-1]
                    elif 'Therefore, the answer is' in answer:
                        extracted_answer = answer.split('Therefore, the answer is')[-1]
                    elif 'Therefore the answer is' in answer:
                        extracted_answer = answer.split('Therefore the answer is')[-1]
                    else:
                        extracted_answer = answer[-200:]
                    
                    # check if description in the extracted answer
                    extracted_answer = extracted_answer.replace("*", "")
                    is_exists = False
                    for option, description in options_dict.items():
                        if description.lower() in extracted_answer.lower():
                            total_acc += 1
                            is_exists = True
                            break
                    if is_exists:
                        continue
                    
                    pattern = r"(?i)([A-G])\)?[\s-]*\{?([^\{\}\(\)]+?)\}?(?=\s*[\(\{\[]?[A-G]\)?]|$)"
                    matches = re.findall(pattern, extracted_answer)

                    # Loop through matches and format them
                    for label, extracted_answer in matches:
                        if gt.upper() == label:
                            total_acc += 1
                        #     print('Answer: ', answer[-200:], 'GT: ', gt)
                        #     print('------------------------------------')
                        # else:
                        #     print('Answer: ', answer[-200:], 'GT: ', gt)
                        #     print('------------------------------------')
                    
                else:
                    if gt in extracted_answer:
                        total_acc += 1
                    else:
                        print("Answer: ", extracted_answer[-100:], 'GT: ', gt)
                        print("====================================")
            else:
                if gt in extracted_answer:
                    total_acc += 1
                else:
                    print("Answer: ", extracted_answer[-100:], 'GT: ', gt)
                    print("====================================")
                
                
             
    
        elif dataset in ['date', 'CLUTRR', 'wikimultihopQA']:
            conclusion = answer.split('{')[-1].split('}')[0]
            
            if conclusion.lower() == gt.lower():
                total_acc += 1
            else:
                if  gt.lower() in answer.lower():
                    total_acc += 1
                else:
                    print("Question: ", question, "Answer: ", answer[-100:], 'GT: ', gt)
                    print("====================================")
        
        elif dataset in ['gpqa']:
            conclusion = answer.split('{')[-1].split('}')[0]
            
            try:
                if float(conclusion) == float(gt):
                    total_acc += 1
                else:
                    print("Question: ", question, "Answer: ", answer[-100:], 'GT: ', gt)
                    print("====================================")
            except:
                continue
                
    # print("The number of failed to follow the format (question, final answer): ", failed_follow_format_question, failed_follow_format_final_answer)
    # print(total_iou/len(questions))
    print(total_acc, len(questions)-failed_follow_format_question-failed_follow_format_final_answer)
    # print("Accuracy: ", total_acc/len(questions))
    print("Accuracy: ", total_acc/(len(questions) - failed_follow_format_question - failed_follow_format_final_answer))

def compute_acc_gsm_plus(questions, answers, gts):

    # load original dataset
    data = read_jsonl_file('../data/GSM_Plus/test.jsonl')

    perturb_dict = {}
    for row in data:
        question = row['question']
        perturbation_type = row['perturbation_type']
        
        if perturbation_type not in perturb_dict:
            perturb_dict[perturbation_type] = 0
        else:
            perturb_dict[perturbation_type] += 1
    print(perturb_dict)

    acc_perturb_dict = {k: 0 for k in perturb_dict.keys()}

    for row in data:
        question = row['question']
        perturbation_type = row['perturbation_type']

        for i, (generated_question, answer, gt) in enumerate(zip(questions, answers, gts)):
            if generated_question == question:
                acc_perturb_dict[perturbation_type] += check_math_answer(answer, gt)
                break
    
    for k, v in acc_perturb_dict.items():
        print(f'{k}: {v/perturb_dict[k]}')

if __name__ == '__main__':
    arg_parser = get_common_args()
    args = arg_parser.parse_args()
    
    # load config file
    # data_path
    with open('../configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    base_data_path = config['base_data_path']
    data_path = os.path.join(base_data_path, config['data_paths'][args.dataset])
    
    data_path = f'../{data_path}'
    result_folder = '../results_auto_tagging'
    
    answer_mode = args.answer_mode
    if args.answer_mode == 'grounding_cot':
        answer_mode = 'design_1_v4'
        
    if args.data_mode == 'random':
        df_path = f'{result_folder}/{args.dataset}/{answer_mode}/fs_inst_{args.llm_model}_temp_10_random.csv'
    else:
        df_path = f'{result_folder}/{args.dataset}/{answer_mode}/fs_inst_{args.llm_model}_temp_10_longest.csv'

    

    df = pd.read_csv(df_path)
    questions = df['question'].tolist()
    answers = df['answer'].tolist()
    ids = df['id'].tolist()
    
    ###
    # questions = questions[:400]
    # answers = answers[:400]
    # ids = ids[:400]
    ###
    if answer_mode == 'design_1_v4':
        # remove all the tags in the answer
        answers = [re.sub(r'</?fact\d+>', '', text) for text in answers]

    gts = retrieve_gts(data_path, ids, args.dataset)
    
    # 
    
    if args.dataset == 'GSM_Plus':
        compute_acc_gsm_plus(questions, answers, gts)
        # compute_acc(questions, answers, gts, args.dataset)
    else:
        compute_acc(questions, answers, gts, args.dataset)