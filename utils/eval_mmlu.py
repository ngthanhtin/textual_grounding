"""Response Parsing and Evaluation for various models"""
from typing import Dict

import sys, os, re, random, yaml
sys.path.insert(0, '../')
random.seed(42)
import numpy as np
import pandas as pd

from arg_parser import get_common_args
from utils import retrieve_gts

from mmlu import parse_open_response, parse_multi_choice_response, check_math_answer, check_aqua_answer, check_asdiv_answer, check_bool_answer, check_exact_match_answer, compute_acc_gsm_plus, check_multiple_choice_answer

from utils import read_jsonl_file


def compute_acc(questions, answers, gts, dataset, tested_questions=None):

    # Append each question and its highlighted answer to the HTML content
    total_acc = 0
    number_non_gts = 0
    
    for i, (question, answer, gt) in enumerate(zip(questions, answers, gts)):
        if dataset == 'ASDiv':
            total_acc += check_asdiv_answer(answer, gt)
        if dataset in ['GSM8K', 'p_GSM8K', 'MultiArith', 'SVAMP', 'GSM8K_Hard', 'GSM_Plus']:
            total_acc += check_math_answer(answer, gt)
        elif dataset in ['AQUA']:
            total_acc += check_aqua_answer(answer, gt)
        elif dataset in ['StrategyQA']:
            total_acc += check_bool_answer(answer, gt)
        elif dataset in ['date', 'wikimultihopQA']:
            total_acc += check_exact_match_answer(answer, gt)
                    
        elif dataset in ['logical_deduction_seven_objects', 'reasoning_about_colored_objects', 'commonsenseQA']:
            total_acc += check_multiple_choice_answer(answer, gt)
                
    print(total_acc, len(questions)-number_non_gts)
    print("Number of non-gts: ", number_non_gts)
    print("Accuracy: ", total_acc/(len(questions)-number_non_gts))

if __name__ == '__main__':
    arg_parser = get_common_args()
    args = arg_parser.parse_args()
    
    # load config file
    # data_path
    with open('../configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    base_data_path = args.base_data_path
    data_path = os.path.join(base_data_path, config['data_paths'][args.dataset])
    
    data_path = f'../{data_path}'
    base_result_path = f'../{args.base_result_path}'
    base_result_path = '../results_auto_tagging'
    
    answer_mode = args.answer_mode
    if args.answer_mode == 'grounding_cot':
        answer_mode = 'design_1_v4'
        
    if args.data_mode == 'random':
        df_path = f'{base_result_path}/{args.dataset}/{answer_mode}/fs_inst_{args.llm_model}_temp_10_random.csv'
    else:
        df_path = f'{base_result_path}/{args.dataset}/{answer_mode}/fs_inst_{args.llm_model}_temp_10_longest.csv'

    
    # batch request eval only supports gpt-4o now
    if not args.batch_request:
        df = pd.read_csv(df_path)
        questions = df['question'].tolist()
        answers = df['answer'].tolist()
        ids = df['id'].tolist()
    else:
        df = pd.read_csv(f'../results_auto_tagging/{args.dataset}/cot/fs_inst_gemini-1.5-pro-002_temp_10_longest.csv')
        questions = df['question'].tolist()
        answers = df['answer'].tolist()
        ids = df['id'].tolist()
        
        batch_output_file = f'../batch_request/{args.dataset}/{args.answer_mode}/batch.jsonl'
        # read jsonl file
        data = read_jsonl_file(batch_output_file)
        answers = []
        for row in data:
            response = row['response']['body']['choices'][0]['message']['content']
            answers.append(response)
    
    # get ids of longest questions
    tested_questions = []
    tested_answers = []
    tested_ids = []
    
    if args.data_mode == 'longest':
        question_length = config['max_question_lengths'][args.dataset]
        for q, a, id in zip(questions, answers, ids):
            if len(q) >= question_length:
                tested_questions.append(q)
                tested_answers.append(a)
                tested_ids.append(id)
    else: # random
        if len(questions) > 200:
            question_length = config['max_question_lengths'][args.dataset]
            
            longest_questions = [q for q in questions if len(q) >= question_length]
            tested_questions = []
            for q, a, id in zip(questions, answers, ids):
                if q not in longest_questions:
                    tested_questions.append(q)
                    tested_answers.append(a)
                    tested_ids.append(id)
            
            # Randomly select 200 unique indices from the lists
            indices = random.sample(range(len(tested_questions)), 200)

            # Create subsets based on the selected indices
            tested_questions = [tested_questions[i] for i in indices]
            tested_answers = [tested_answers[i] for i in indices]
            tested_ids = [tested_ids[i] for i in indices]
        else:
            tested_questions = questions
            tested_answers = answers
            tested_ids = ids
    
    print("Length of tested question: ", len(tested_questions))
    questions = tested_questions
    answers = tested_answers
    ids = tested_ids
    
    gts = retrieve_gts(data_path, ids, args.dataset)
    
    if args.dataset == 'GSM_Plus':
        # compute_acc_gsm_plus(questions, answers, gts)
        compute_acc(questions, answers, gts, args.dataset, tested_questions=tested_questions)
    else:
        compute_acc(questions, answers, gts, args.dataset, tested_questions=tested_questions)