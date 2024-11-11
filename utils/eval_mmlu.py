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
            
            all_choices = list(index2ans.keys())
            pred_index = parse_multi_choice_response(answer, all_choices, index2ans)
            
            gt_number  = index2ans[gt]
            
            if pred_index.lower() == gt.lower():
                total_acc += 1
            else:
                # Regular expression to capture the answer option
                match = re.search(r"\*\*(.*?)\*\*", answer)
                if match:
                    answer_option = match.group(1)
                    if gt.lower() in answer_option.lower():
                        total_acc += 1
                    else:
                        print('Answer: ', answer[-100:], 'GT: ', gt, gt_number)
                        print('------------------------------------')
                else:    
                    if gt_number in answer[-50:]:
                        total_acc += 1
                    else:
                        print('Answer: ', answer[-100:], 'GT: ', gt, gt_number)
                        print('------------------------------------')
             
        
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
                
    print("The number of failed to follow the format (question, final answer): ", failed_follow_format_question, failed_follow_format_final_answer)
    # print(total_iou/len(questions))
    print(total_acc, len(questions)-failed_follow_format_question-failed_follow_format_final_answer)
    # print("Accuracy: ", total_acc/len(questions))
    print("Accuracy: ", total_acc/(len(questions) - failed_follow_format_question - failed_follow_format_final_answer))

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

    # df_path = f'../results/{args.dataset}/cot/fs_inst_claude_temp_0.csv'

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
    
    compute_acc(questions, answers, gts, args.dataset)