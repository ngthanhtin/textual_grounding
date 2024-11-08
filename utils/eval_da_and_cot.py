
import pandas as pd
from utils import retrieve_gts
import argparse

def compute_acc(questions, answers, gts, dataset, prefix):

    # Append each question and its highlighted answer to the HTML content
    total_iou = 0
    total_acc = 0
    avg_grounding_question = 0
    avg_grounding_answer = 0
    avg_len_grounding_question = 0
    avg_len_grounding_answer = 0
    failed_follow_format_question = 0
    failed_follow_format_final_answer = 0

    for i, (question, answer, gt) in enumerate(zip(questions, answers, gts)):
        
        # answer is in the format Answer: {answer}        
        # try:
        #     answer = answer.split('Answer')[1].strip()
        # except:
        #     failed_follow_format_final_answer += 1
        #     print(answer, "GT: ", gt)
        #     # print('----')
        #     continue

        
        if dataset in ['SVAMP']:
            conclusion = answer.split('{')[-1].split('}')[0]
            conclusion = conclusion.replace("*", "").replace("$", "").replace(",", "").replace("€", "").replace('%', '')
            try:
                if conclusion[-1] == '.':
                    conclusion = conclusion[:-1]
            except:
                failed_follow_format_final_answer += 1
                # print(answer, "GT: ", gt)
                # print('----')
                continue
            
            try:    
                if float(conclusion) == gt:
                    total_acc += 1
                # else:
                #     print(question, "Answer: ", original_answer, "GT: ", gt)
                #     print('----')
            except:
                # print(answer)
                # print(conclusion, gt)
                failed_follow_format_final_answer += 1
                # print(answer, "GT: ", gt)
                print('----')
                continue
        if dataset in ['date', 'CLUTRR']:
            conclusion = answer.split('{')[-1].split('}')[0]
            try:
                if conclusion == gt:
                    total_acc += 1
            except:
                failed_follow_format_final_answer += 1
                # print(answer, "GT: ", gt)
                print('----')
                continue
        if dataset in ['GSM8K', 'p_GSM8K', 'MultiArith', 'ASDiv']:
            conclusion = answer.split('{')[-1].split('}')[0]
            conclusion = conclusion.replace(":", "").replace("*", "").replace("$", "").replace(",", "").replace("{", "").replace("}", "").replace("€", "").replace('%', '')
            conclusion = conclusion.strip()
            try:
                if conclusion[-1] == '.':
                    conclusion = conclusion[:-1]
            except:
                failed_follow_format_final_answer += 1
                # print(answer, "GT: ", gt)
                print('----')
                continue
            
            try:    
                if float(conclusion) == gt:
                    total_acc += 1
                # else:
                #     print(question, "Answer: ", original_answer, "GT: ", gt)
                #     print('----')
            except:
                # print(answer)
                print(conclusion, gt)
                failed_follow_format_final_answer += 1
                # print(answer, "GT: ", gt)
                print('----')
                continue
        elif dataset in ['StrategyQA', 'sports']:
            conclusion = answer.split('{')[-1].split('}')[0]
            conclusion = conclusion.replace(":", "").replace("{", "").replace("}", "")
            
            if conclusion.lower() in ['yes', 'true', '1']:
                conclusion = True
            elif conclusion.lower() in ['no', 'false', '0']:
                conclusion = False
            
            if bool(conclusion) == bool(gt):
                total_acc += 1
            else:
                # print(question, "Answer: ", original_answer, "GT: ", gt)
                print(conclusion, gt)
                print('----')
        elif dataset in ['AQUA', 'commonsenseQA']:
            # conclusion = answer.split('{')[-1].split('}')[0]
            
            if '{' in answer:
                conclusion = answer.split('{')[1].split('}')[0]
            elif 'the answer is' in answer.lower():
                conclusion = answer.lower().split('the answer is')[1].strip()
            elif 'the correct answer is' in answer.lower():
                conclusion = answer.lower().split('the correct answer is')[1].strip()
                
            try:
                # if conclusion[0] == 'A':
                #     conclusion = 'A'
                # elif conclusion[0] == 'B':
                #     conclusion = 'B'
                # elif conclusion[0] == 'C':
                #     conclusion = 'C'
                # elif conclusion[0] == 'D':
                #     conclusion = 'D'
                # elif conclusion[0] == 'E':
                #     conclusion = 'E'
                
                if 'A' in conclusion or 'a' in conclusion:
                    conclusion = 'A'
                elif 'B' in conclusion or 'b' in conclusion:
                    conclusion = 'B'
                elif 'C' in conclusion or 'c' in conclusion:
                    conclusion = 'C'
                elif 'D' in conclusion or 'd' in conclusion:
                    conclusion = 'D'
                elif 'E' in conclusion or 'e' in conclusion:
                    conclusion = 'E'
            except:
                failed_follow_format_final_answer += 1
                print(answer, gt)
                print('----')
                continue
            if conclusion.lower() == gt.lower():
                total_acc += 1
            else:
                # print(question, "Answer: ", original_answer, "GT: ", gt)
                print(conclusion, gt)
                print('----')
        
    print("The number of failed to follow the format (question, final answer): ", failed_follow_format_question, failed_follow_format_final_answer)
    # print(total_iou/len(questions))
    print(total_acc, len(questions)-failed_follow_format_question-failed_follow_format_final_answer)
    print("Accuracy: ", total_acc/len(questions))

# %%
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--llm_model', type=str, default='gemini', help='The language model to query', choices=['gemini-1.5-pro-002', 'gemini-1.5-flash-002', 'claude', 'gpt-4o-2024-08-06', 'gpt-4o-mini-2024-07-18', 'llama_transformer', 'llama_groq'])
    arg_parser.add_argument('--dataset', type=str, default='GSM8K', help='The dataset to query', choices=['GSM8K', 'StrategyQA', 'p_GSM8K', 'AQUA', 'MultiArith', 'ASDiv', 'SVAMP', 'commonsenseQA', 'date', 'sports', 'reclor', 'CLUTRR'])
    arg_parser.add_argument('--prompt_used', type=str, default='fs_inst', help='The prompt used to query the language model', choices=['zs', 'fs', 'fs_inst'])
    arg_parser.add_argument('--answer_mode', type=str, default='design_1_v4', help='The answer mode', choices=['da', 'cot', 'design_1_v4'])
    arg_parser.add_argument('--save_answer', action='store_true')
    arg_parser.add_argument('--data_mode', type=str, default='longest', help='The data mode', choices=['random', 'longest'])
    args = arg_parser.parse_args()
    

    if args.dataset == 'p_GSM8K':
        data_path = f'../data/{args.dataset}/r-gsm.jsonl'    
    else:
        data_path = f'../data/{args.dataset}/test.jsonl'

    if args.data_mode == 'random':
        df_path = f'../results/{args.dataset}/{args.answer_mode}/fs_inst_{args.llm_model}_temp_0_random.csv'
    else:
        df_path = f'../results/{args.dataset}/{args.answer_mode}/fs_inst_{args.llm_model}_temp_0.csv'

    # df_path = f'../results/{args.dataset}/{args.answer_mode}/fs_inst_claude_temp_0.csv'
    prefix = 'Answer'

    
    df = pd.read_csv(df_path)
    questions = df['question'].tolist()
    answers = df['answer'].tolist()
    ids = df['id'].tolist()
    gts = retrieve_gts(data_path, ids, args.dataset)
    
    compute_acc(questions, answers, gts, args.dataset, prefix)