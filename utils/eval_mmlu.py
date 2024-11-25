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

def compute_acc(questions, answers, gts, dataset):
    # Append each question and its highlighted answer to the HTML content
    total_acc = 0
    failed_follow_format_question = 0
    failed_follow_format_final_answer = 0
    # print(f"questions: {questions}")
    # print(f"answers: {answers}")
    # print(f"gts: {gts}")
    print("Dataset: ", dataset)
    for i, (question, answer, gt) in enumerate(zip(questions, answers, gts)):
        # print("Dataset: ", dataset) 
        # print("Question: ", question, "Answer: ", answer, 'GT: ', gt)
        if dataset in ['GSM8K', 'p_GSM8K', 'MultiArith', 'SVAMP', 'ASDiv', 'GSM8K_Hard', 'GSM_Plus', 'SPARTQA']:
            total_acc += check_math_answer(answer, gt)
            
        elif dataset in ['AQUA', 'reasoning_about_colored_objects', 'logical_deduction_seven_objects', 'commonsenseQA', 'medqa']:
            index2ans = parse_options(question, dataset)
            # remove ' in index2ans
            index2ans = {key: value.replace("'", "") for key, value in index2ans.items()}
            
            # all_choices = list(index2ans.keys())
            # pred_index = parse_multi_choice_response(answer, all_choices, index2ans)
            
            gt_number  = index2ans[gt]
            
            try:
                extracted_answer = answer.split('{')[-1].split('}')[0]
                if gt.upper() in extracted_answer or gt_number in extracted_answer:
                    total_acc += 1
                    print('Answer: ', answer[-200:], 'GT: ', gt, gt_number)
                    print('------------------------------------')
                else:
                    # print('------------------------------------')
                    # print(question)
                    # print('Incorrect Answer: ', answer[-100:], 'GT: ', gt, gt_number)
                    # print('GT: ', gt, gt_number)
                    # print('------------------------------------')
                    pass
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
                        # print('incorrect Answer: ', answer[-200:], 'GT: ', gt, gt_number)
                        # print('------------------------------------')
                        pass

    
        # elif dataset in ['reasoning_about_colored_objects', 'logical_deduction_seven_objects']:
        #     try:
        #         extracted_answer = answer.split('{')[-1].split('}')[0]
        #         if gt in extracted_answer:
        #             total_acc += 1
        #             # print('Answer: ', answer[-200:], 'GT: ', gt, gt_number)
        #             # print('------------------------------------')
        #         else:
        #             # print('Answer: ', answer[-200:], 'GT: ', gt, gt_number)
        #             # print('------------------------------------')
        #     except:
        #         try:
        #             extracted_answer = answer.split('(')[-1].split(')')[0]
        #             if gt in extracted_answer:
        #                 total_acc += 1
        #                 print('Answer: ', answer[-200:], 'GT: ', gt, gt_number)
        #                 print('------------------------------------')
        #             else:
        #                 print('Answer: ', answer[-200:], 'GT: ', gt, gt_number)
        #                 print('------------------------------------')
        #         except:
        #             if 'The closest answer option is' in answer:
        #                 extracted_answer = answer.split('The closest answer option is')[-1]
        #             elif'The correct answer is' in answer:
        #                 extracted_answer = answer.split('The correct answer is')[-1]
        #             elif 'Therefore, the answer is' in answer:
        #                 extracted_answer = answer.split('Therefore, the answer is')[-1]
        #             elif 'Therefore the answer is' in answer:
        #                 extracted_answer = answer.split('Therefore the answer is')[-1]
        #             else:
        #                 extracted_answer = answer[-200:]
                    
        #             pattern = r"(?i)([A-G])\)?[\s-]*\{?([^\{\}\(\)]+?)\}?(?=\s*[\(\{\[]?[A-G]\)?]|$)"
        #             matches = re.findall(pattern, extracted_answer)

        #             # Loop through matches and format them
        #             for label, extracted_answer in matches:
        #                 if gt.upper() == label:
        #                     total_acc += 1
        #                     print('Answer: ', answer[-200:], 'GT: ', gt)
        #                     print('------------------------------------')
        #                 else:
        #                     print('Answer: ', answer[-200:], 'GT: ', gt)
        #                     print('------------------------------------')
                
                
             
    
        elif dataset in ['date', 'CLUTRR', 'wikimultihopQA']:
            conclusion = answer.split('{')[-1].split('}')[0]
            
            if conclusion.lower() == gt.lower():
                total_acc += 1
            else:
                if  gt.lower() in answer.lower():
                    total_acc += 1
                # else:
                #     # print("Question: ", question, "Answer: ", answer[-100:], 'GT: ', gt)
                #     print("====================================")
        
        elif dataset in ['gpqa']:
            conclusion = answer.split('{')[-1].split('}')[0]
            
            try:
                if float(conclusion) == float(gt):
                    total_acc += 1
                else:
                    # print("Question: ", question, "Answer: ", answer[-100:], 'GT: ', gt)
                    print("====================================")
            except:
                continue
                
    # print("The number of failed to follow the format (question, final answer): ", failed_follow_format_question, failed_follow_format_final_answer)
    # print(total_iou/len(questions))
    print(total_acc, len(questions)-failed_follow_format_question-failed_follow_format_final_answer)
    # print("Accuracy: ", total_acc/len(questions))
    result = total_acc/(len(questions))
    print("Accuracy: ", round(result, 4)*100)
    print("------------------------------------")

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

def evaluate_model(llm_model: str, data_mode: str, answer_mode: str, dataset: str):

    
    # load config file
    # data_path
    with open('../configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    base_data_path = '/Users/log/Github/textual_grounding/data/'
    data_path = os.path.join(base_data_path, config['data_paths'][dataset])

    result_folder = '../results_auto_tagging'
    
    answer_mode = answer_mode
    if answer_mode == 'grounding_cot':
        answer_mode = 'design_1_v4'
        
    if data_mode == 'random':
        df_path = f'{result_folder}/{dataset}/{answer_mode}/fs_inst_{llm_model}_temp_10_random.csv'
    else:
        # df_path = f'{result_folder}/{args.dataset}/{answer_mode}/fs_inst_{args.llm_model}_temp_10_longest.csv'
        df_path = f'/Users/log/Github/textual_grounding/logan/results/final/GCoT/{dataset}/{llm_model}/gcot_shortest_gcot_examples.txt_{dataset}_{llm_model}.csv'

    

    df = pd.read_csv(df_path)
    questions = df['question'].tolist()
    # questions = df['prompt'].tolist()
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

    gts = retrieve_gts(data_path, ids, dataset)
    
    # 
    # print(len(questions), len(answers), len(gts), len(ids))
    
    if dataset == 'GSM_Plus':
        compute_acc_gsm_plus(questions, answers, gts)
        # compute_acc(questions, answers, gts, args.dataset)
    else:
        compute_acc(questions, answers, gts, dataset)
