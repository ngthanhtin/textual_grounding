import sys, os, re, random, yaml
sys.path.insert(0, '../')
random.seed(42)
import numpy as np
import pandas as pd

from arg_parser import get_common_args


from utils.eval_parser import check_math_answer, check_aqua_answer, check_asdiv_answer, check_bool_answer, check_exact_match_answer, check_multiple_choice_answer, check_gsm_hard_answer, check_drop_answer, check_squad_answer, check_medQA_answer

from utils import read_jsonl_file
from load_dataset import DatasetLoader

# compute avg length of a list of strings
def avg_len(inputs):
    avg_len = 0
    for a in inputs:
        avg_len += len(a)
    avg_len = avg_len/len(inputs)
    return avg_len
    
def compute_acc(questions, answers, gts, dataset, verbose=False):

    # Append each question and its highlighted answer to the HTML content
    total_acc = 0
    total_questions = 0
    for i, (question, answer, gt) in enumerate(zip(questions, answers, gts)):
        is_correct = 0
        if dataset == 'ASDiv':
            is_correct += check_asdiv_answer(answer, gt)
        elif dataset == 'GSM8K_Hard':
            is_correct += check_gsm_hard_answer(answer, gt)
        elif dataset in ['GSM8K', 'GSM_Symbolic', 'p_GSM8K', 'MultiArith', 'SVAMP', 'GSM_Plus']:
            is_correct += check_math_answer(answer, gt)
        elif dataset in ['AQUA']:
            is_correct += check_aqua_answer(question, answer, gt)
        elif dataset in ['StrategyQA', 'navigate', 'causal_judgement', 'web_of_lies']:
            is_correct += check_bool_answer(answer, gt)
        elif dataset in ['date', 'wikimultihopQA']:
            is_correct += check_exact_match_answer(answer, gt)
        elif dataset == 'squad':
            is_correct += check_squad_answer(answer, gt)
        elif dataset in ['logical_deduction_three_objects', 'logical_deduction_five_objects', 'logical_deduction_seven_objects', 'reasoning_about_colored_objects', 'commonsenseQA', 'spartQA', 'tracking_shuffled_objects_seven_objects', 'temporal_sequences']:
            is_correct += check_multiple_choice_answer(question, answer, gt)
        elif dataset in ['drop_break', 'drop_cencus']:
            if len(gt) >= 2:
                gt = [gt[-1]]
            total_questions += 1
            is_correct += check_drop_answer(answer, gt)
        elif dataset == 'medQA':
            is_correct += check_medQA_answer(question, answer, gt)
        total_acc += is_correct
        
        verbose=False
        if verbose:
            if is_correct == 0:
                print("Index: ", i, "Answer: ", answer[-100:], 'GT: ', gt)
                print("====================================")
                
    print(total_acc, len(questions))
    print("Accuracy: ", total_acc/(len(questions)))
    
    # print(total_acc, total_questions)
    # print("Accuracy: ", total_acc/total_questions)
    
    return total_acc/(len(questions)), total_acc

if __name__ == '__main__':
    arg_parser = get_common_args()
    args = arg_parser.parse_args()
    
    # List out all the datasets (medQA)
    # datasets = ['GSM8K', 'MultiArith', 'ASDiv', 'SVAMP', 'AQUA', 'GSM8K_Hard', 'StrategyQA', 'spartQA', 'date', 'p_GSM8K', 'GSM_Plus', 'logical_deduction_five_objects', 'logical_deduction_seven_objects', 'reasoning_about_colored_objects', 'causal_judgement', 'navigate', 'drop_break', 'drop_cencus', 'squad']
    
    datasets = ['GSM8K', 'MultiArith', 'ASDiv', 'SVAMP', 'AQUA', 'StrategyQA', 'date', 'p_GSM8K', 'logical_deduction_five_objects', 'logical_deduction_seven_objects', 'reasoning_about_colored_objects', 'causal_judgement', 'navigate']
    
    datasets = ['StrategyQA']
    # datasets = ['logical_deduction_seven_objects']
    # datasets = ['AQUA', 'p_GSM8K', 'logical_deduction_seven_objects', 'navigate']
    # datasets = ['GSM_Symbolic']
    # datasets = ['spartQA']
    # "gpt-4o-2024-08-06", "llama_sambanova_8b",
    llm_models = ["gemini-1.5-flash-002", "gemini-1.5-pro-002", "llama_sambanova_70b", "llama_sambanova_405b"]
    # llm_models = ["gemini-1.5-flash-002", "gemini-1.5-pro-002", "llama_sambanova_70b", "llama_sambanova_405b"]
    # llm_models = ["gemini-1.5-flash-002"]
    # llm_models = ["gemini-1.5-pro-002"]
    # llm_models = ["llama_sambanova_405b"]
    # llm_models = ["llama_sambanova_8b"]
    llm_models = ["llama_sambanova_70b"]
    # llm_models = ["gpt-4o-2024-08-06"]
    # llm_models = ["qwen25_coder_32b"]
    # llm_models = ["qwq_32b"]
    
    answer_modes = ['cot', 'design_1_v4']
    # answer_modes = ['design_1_v4']
    # answer_modes = ['cot']
    
    # data_modes = ['shortest', 'longest', 'full']
    # data_modes = ['longest']   
    data_modes = ['longest']   
    tail = ''
    # tail = '_random_tag_Q'
    # tail = '_v2'
    # tail = '_only_ground_A'
    # tail = '_only_ground_Q'
    # tail = '_repeat_Q'
    # tail = '_number_tag'
    
    
    dict_acc = {k: {d: {'cot': 0, 'grounding_cot': 0} for d in datasets}  for k in llm_models}
    
    for llm_model in llm_models:
        print(f"Model: {llm_model}")
        for dataset in datasets:
            print(f"Dataset: {dataset}")
            for answer_mode in answer_modes:
                    for data_mode in data_modes:
                        # 1/ read data
                        dataloader = DatasetLoader(config_path='../configs/config.yaml', base_data_path=f'../{args.base_data_path}', base_few_shot_prompt_path=args.base_prompt_path, dataset=dataset, data_mode=data_mode, num_samples=args.num_samples)
                        
                        longest_questions, longest_ids = dataloader.get_longest_questions_and_ids()
                        
                        # random_questions, random_ids = dataloader.get_random_questions_and_ids()
                        shortest_questions, shortest_ids = dataloader.get_shortest_questions_and_ids()
                        # 2/ read results
                        base_result_path = f'../{args.base_result_path}'
                        base_result_path = '../results_auto_tagging'
                        str_temperature = str(args.temperature).replace('.', '')
                        df_path = f'{base_result_path}/{dataset}/{answer_mode}/fs_inst_{llm_model}_temp_{str_temperature}_{data_mode}{tail}.csv'
                        if not os.path.exists(df_path):
                            df_path = df_path.replace('shortest', 'longest') #### temporary
                        ## batch request eval only supports gpt-4o now
                        if not args.batch_request:
                            print(df_path)
                            df = pd.read_csv(df_path)
                            questions = df['question'].tolist()
                            answers = df['answer'].tolist()
                            ids = df['id'].tolist()
                            # ids = [id for id in ids]
                            
                            # if dataset == 'GSM_Symbolic':
                            #     ids = [i for i in range(len(ids))]
                        else:
                            # df = pd.read_csv(f'../results_auto_tagging_3/{dataset}/cot/fs_inst_gemini-1.5-pro-002_temp_10_longest.csv')
                            # questions = df['question'].tolist()
                            # answers = df['answer'].tolist()
                            # ids = df['id'].tolist()
                            
                            batch_output_file = f'../batch_request/{dataset}/{answer_mode}/batch.jsonl'
                            if answer_mode == 'design_1_v4':
                                batch_output_file = f'../batch_request/{dataset}/grounding_cot/batch.jsonl'    
                            
                            # read jsonl file
                            data = read_jsonl_file(batch_output_file)
                            
                            answers = []
                            ids = []
                            for row in data:
                                response = row['response']['body']['choices'][0]['message']['content']
                                id = row['custom_id'].replace('task-', '')
                                answers.append(response)
                                ids.append(id)
                            
                            if dataset in ['spartQA', 'logical_deduction_five_objects', 'GSM_Symbolic']:
                                ids = [int(id) for id in ids]
                                
                            questions = dataloader.get_questions_with_ids(ids)
                            
                            gts = dataloader.retrieve_gts(ids)
                            print(f"Accuracy of {dataset} of {answer_mode} of {llm_model}:")
                            acc, num_correct_answers = compute_acc(questions, answers, gts, dataset, verbose=True)
                            print('--------------------------------------')
                            break
                            
                        # 3/ read gts
                        longest_answers = []
                        shortest_answers = []
                        random_answers = []
                        
                        if data_mode == 'longest':
                            for q, id in zip(longest_questions, longest_ids):
                                if id in ids:
                                    longest_answers.append(answers[ids.index(id)])
                                
                            gts_for_longest_questions = dataloader.retrieve_gts(longest_ids)
                            
                            print("Accuracy for Longest questions:")
                            acc, num_correct_answer = compute_acc(longest_questions, longest_answers, gts_for_longest_questions, dataset, verbose=True)
                        elif data_mode == 'shortest':
                            for q, id in zip(shortest_questions, shortest_ids):
                                if id in ids:
                                    shortest_answers.append(answers[ids.index(id)])
                                
                            gts_for_shortest_questions = dataloader.retrieve_gts(shortest_ids)
                            
                            print("Accuracy for Shortest questions:")
                            acc, num_correct_answer = compute_acc(shortest_questions, shortest_answers, gts_for_shortest_questions, dataset, verbose=True)
                        elif data_mode == 'full':
                            gts_full = dataloader.retrieve_gts(ids)
                            print(f"Accuracy for Full questions of {dataset} of {answer_mode} of {llm_model}:")
                            acc, num_correct_answers = compute_acc(questions, answers, gts_full, dataset, verbose=True)
                        
                        print('--------------------------------------')
                        
                        # dict_acc[llm_model][dataset][answer_mode] = acc
                        
    # save to csv
    
    # Loop through each LLM model to create and save a CSV file
    # for llm_model, dataset_data in dict_acc.items():
    #     # Prepare data for DataFrame
    #     df = pd.DataFrame(
    #     {dataset: {'cot': round(dataset_data[dataset]['cot']*100, 2), 'gcot': round(dataset_data[dataset]['design_1_v4']*100, 2)} 
    #      for dataset in datasets}
    #     )
    
    #     # df = df.T  # Transpose the DataFrame
    #     df.index.name = "Dataset"  # Name the index
    #     df.reset_index(inplace=True)  
        
        # Save to CSV
        # file_name = f"acc_longest_all/{llm_model}_results.csv"
        # df.to_csv(file_name, index=False)
        # print(f"Saved {file_name}")
        