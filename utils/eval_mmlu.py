import sys, os, re, random, yaml
sys.path.insert(0, '../')
random.seed(42)
import numpy as np
import pandas as pd

from arg_parser import get_common_args


from mmlu import check_math_answer, check_aqua_answer, check_asdiv_answer, check_bool_answer, check_exact_match_answer, check_multiple_choice_answer

from utils import read_jsonl_file
from load_dataset import DatasetLoader

def compute_acc(questions, answers, gts, dataset, verbose=False):

    # Append each question and its highlighted answer to the HTML content
    total_acc = 0
    
    for i, (question, answer, gt) in enumerate(zip(questions, answers, gts)):
        is_correct = 0
        if dataset == 'ASDiv':
            is_correct += check_asdiv_answer(answer, gt)
        elif dataset in ['GSM8K', 'p_GSM8K', 'MultiArith', 'SVAMP', 'GSM_Plus', 'GSM8K_Hard', 'drop_break', 'drop_cencus']:
            is_correct += check_math_answer(answer, gt)
        elif dataset in ['AQUA']:
            is_correct += check_aqua_answer(question, answer, gt)
        elif dataset in ['StrategyQA', 'navigate', 'causal_judgement', 'web_of_lies']:
            is_correct += check_bool_answer(answer, gt)
        elif dataset in ['date', 'wikimultihopQA']:
            is_correct += check_exact_match_answer(answer, gt)
        elif dataset == 'squad':
            if gt in answer or answer in gt:
                is_correct += 1
        elif dataset in ['logical_deduction_three_objects', 'logical_deduction_five_objects', 'logical_deduction_seven_objects', 'reasoning_about_colored_objects', 'commonsenseQA', 'spartQA', 'tracking_shuffled_objects_seven_objects', 'temporal_sequences']:
            is_correct += check_multiple_choice_answer(question, answer, gt)
    
        total_acc += is_correct
        
        verbose=False
        if verbose:
            if is_correct == 0:
                print("Index: ", i, "Answer: ", answer[-100:], 'GT: ', gt)
                print("====================================")
                
    print(total_acc, len(questions))
    print("Accuracy: ", total_acc/(len(questions)))
    
    return total_acc/(len(questions)), total_acc

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

    
    args.data_mode = 'longest'
    df_path = f'{base_result_path}/{args.dataset}/{answer_mode}/fs_inst_{args.llm_model}_temp_10_{args.data_mode}.csv'
    
    if args.dataset == 'AQUA':
        args.num_samples = 254//2
    elif args.dataset == 'date':
        args.num_samples = 359//2
    elif args.dataset == 'p_GSM8K':
        args.num_samples = 100
    elif args.dataset in ['logical_deduction_seven_objects', 'reasoning_about_colored_objects']:
        args.num_samples = 250//2
        
    dataloader = DatasetLoader(config_path='../configs/config.yaml', base_data_path=f'../{args.base_data_path}', base_few_shot_prompt_path=args.base_prompt_path, dataset=args.dataset, data_mode=args.data_mode, num_samples=args.num_samples)
    
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
        
        batch_output_file = f'../batch_request_results/{args.dataset}/{args.answer_mode}/batch.jsonl'
        # read jsonl file
        data = read_jsonl_file(batch_output_file)
        answers = []
        for row in data:
            response = row['response']['body']['choices'][0]['message']['content']
            answers.append(response)
    
    longest_questions, longest_ids = dataloader.get_longest_questions_and_ids()
    random_questions, random_ids = dataloader.get_random_questions_and_ids()
    print(len(longest_questions), len(random_questions), len(questions))
    shortest_questions, shortest_ids = dataloader.get_shortest_questions_and_ids()
    
    longest_answers = []
    shortest_answers = []
    random_answers = []
    for q, id in zip(longest_questions, longest_ids):
        if id in ids:
            longest_answers.append(answers[ids.index(id)])
    for q, id in zip(shortest_questions, shortest_ids):
        if id in ids:
            shortest_answers.append(answers[ids.index(id)])
    for q, id in zip(random_questions, random_ids):
        if id in ids:
            random_answers.append(answers[ids.index(id)])
    
    gts_for_longest_questions = dataloader.retrieve_gts(longest_ids)
    gts_for_random_questions = dataloader.retrieve_gts(random_ids)
    gts_for_shortest_questions = dataloader.retrieve_gts(shortest_ids)
    gts_full = dataloader.retrieve_gts(ids)
    
    # compute avg length of answer
    def avg_len(inputs):
        avg_len = 0
        for a in inputs:
            avg_len += len(a)
        avg_len = avg_len/len(inputs)
        return avg_len
    
    # print("Avg length of random answer: ", avg_len(random_answers))
    # print("Avg length of longest answer: ", avg_len(longest_answers))
    # print("Avg length of shortest answer: ", avg_len(shortest_answers))
    
    # print("Avg length of random question: ", avg_len(random_questions))
    print("Avg length of longest question: ", avg_len(longest_questions))
    print("Avg length of shortest question: ", avg_len(shortest_questions))
    
    
    
    # exit()
    # print("Accuracy for Random questions:")
    # compute_acc(random_questions, random_answers, gts_for_random_questions, args.dataset, verbose=True)
    # print("Accuracy for Longest questions:")
    # compute_acc(longest_questions, longest_answers, gts_for_longest_questions, args.dataset, verbose=True)
    
    print(len(shortest_questions))
    print("Accuracy for Shortest questions:")
    a, b = compute_acc(shortest_questions, shortest_answers, gts_for_shortest_questions, args.dataset, verbose=True)
    print("The number of correct answers: ", b)
    
    print(len(longest_questions))
    print("Accuracy for Longest questions:")
    a,b = compute_acc(longest_questions, longest_answers, gts_for_longest_questions, args.dataset, verbose=True)
    print("The number of correct answers: ", b)
    
    # print("Accuracy for Full questions:")
    # compute_acc(questions, answers, gts_full, args.dataset, verbose=True)
    print('--------------------------------------')
    
    # if args.dataset == 'GSM_Plus':
    #     # compute_acc_gsm_plus(questions, answers, gts)
    #     compute_acc(questions, answers, gts, args.dataset)
    # else:
    #     compute_acc(questions, answers, gts, args.dataset, verbose=True)