
# %%
import pandas as pd
from utils import extract_parts_1, calculate_iou, add_color_to_tags, extract_conclusion, extract_parts_only_answer, check_for_word, read_jsonl_file, parse_open_response
import argparse

# %%
def compute_acc(questions, answers, gts, dataset, prefix):
    total_iou = 0
    total_acc = 0
    avg_grounding_question = 0
    avg_grounding_answer = 0
    avg_len_grounding_question = 0
    avg_len_grounding_answer = 0
    failed_follow_format_question = 0
    failed_follow_format_final_answer = 0

    total_acc_mmlu = 0

    for i, (question, answer, gt) in enumerate(zip(questions, answers, gts)):
        original_answer = answer
        try:
            reformulated_question, extracted_answer = extract_parts_1(answer)
            # extracted_answer = extract_parts_only_answer(answer)
            # reformulated_question = ''
        except:
            failed_follow_format_question += 1
            continue
        iou, question_tags, answer_tags = calculate_iou(reformulated_question, extracted_answer)
        
        pred_lists = parse_open_response(extracted_answer)
        
        if gt in pred_lists:
            total_acc_mmlu += 1
            
        
        # if len(question_tags) == 0:
        #     failed_follow_format_question += 1
        #     continue
        # if len(answer_tags) == 0:
        #     print('here')
        #     failed_follow_format_final_answer += 1
        #     continue
            
        len_question_tag, len_answer_tag = len(question_tags), len(answer_tags)
        avg_grounding_question+=len_question_tag
        avg_grounding_answer+=len_answer_tag
        
        # total_tag_question_legth = 0
        # for tag in question_tags:
        #     total_tag_question_legth+= len(tag[1])
        # avg_len_grounding_question+=total_tag_question_legth/len(question_tags)
        
        # total_tag_answer_legth = 0
        # for tag in answer_tags:
        #     total_tag_answer_legth+= len(tag[1])
        # avg_len_grounding_answer+=total_tag_answer_legth/len(answer_tags)
        
        if dataset == 'date':
            try:
                answer = answer.split('{')[1].split('}')[0]
            except:
                failed_follow_format_final_answer += 1
                print(answer, gt)
                print('----')
                continue
            if answer == gt:
                total_acc += 1
            else:
                print(question, "Answer: ", original_answer, "GT: ", gt)
                print('----')
        if dataset in ['GSM8K', 'p_GSM8K', 'MultiArith', 'ASDiv', 'SVAMP']:
            answer = answer.replace("*", "").replace("$", "").replace("€", "").replace('%', '')
            # conclusion = extract_conclusion(answer.lower(), prefix.lower())   
            # conclusion = conclusion.replace(f'{prefix.lower()}', '')
            # the answer is inside {}
            try:
                conclusion = answer.split('{')[1].split('}')[0]
                # print(conclusion, gt)
            except:
                print(answer[50:], gt)
                print('----')
                failed_follow_format_final_answer += 1
                continue
            
            conclusion = conclusion.strip()
            try:
                if conclusion[-1] == '.':
                    conclusion = conclusion[:-1]
            except:
                failed_follow_format_final_answer += 1
                print(answer[50:], gt)
                print('----')
                continue
            
            try:
                if ',' in conclusion:
                    conclusion = conclusion.replace(',', '')
                if '$' in conclusion:
                    conclusion = conclusion.replace('$', '')
                    
                if float(conclusion) == gt:
                    total_acc += 1
                # else:
                #     print(question, "Answer: ",original_answer , "GT: ", gt)
            except:
                print(answer[50:], gt)
                print('----')
                failed_follow_format_final_answer += 1
                continue
        
        if dataset in ['StrategyQA', 'sports']:
            try:
                answer = answer.split('{')[1].split('}')[0]
            except:
                try:                    
                    if any(x in answer.lower() for x in [' no', 'no ', 'false']):
                        bool_answer = False
                    elif any(x in answer.lower() for x in [' yes', 'yes ', 'true']):
                        bool_answer = False
                    
                    if bool(bool_answer) == bool(gt):
                        total_acc += 1
                        continue
                    else:
                        print(bool_answer, gt)
                except:
                    
                    failed_follow_format_final_answer += 1
                    print(original_answer, gt)
                    print('-----')
                    continue
            if answer.lower() in ['yes', 'true', '1']:
                answer = True
            elif answer.lower() in ['no', 'false', '0']:
                answer = False
            if bool(answer) == bool(gt):
                total_acc += 1
            else:
                print(bool(answer), gt)
                print('----')
        if dataset in ['AQUA', 'commonsenseQA']:
            try:
                answer = answer.split('{')[1].split('}')[0]
            except:
                try:
                    answer = answer.lower().split('the answer is')[1].split('(')[1].split(')')[0]
                    # if answer[0] == '(':
                    #     answer = answer.split('(')[1].split(')')[0]
                    # else:
                    #     answer = answer[0]
                except:
                    failed_follow_format_final_answer += 1
                    print(answer, gt)
                    print('----')
                    continue
            try:
                if answer[0] == 'A':
                    conclusion = 'A'
                elif answer[0] == 'B':
                    conclusion = 'B'
                elif answer[0] == 'C':
                    conclusion = 'C'
                elif answer[0] == 'D':
                    conclusion = 'D'
                elif answer[0] == 'E':
                    conclusion = 'E'
                    
                if conclusion.lower() == gt.lower():
                    total_acc += 1
                else:
                    # print(question, "Answer: ", original_answer, "GT: ", gt)
                    print(conclusion, gt)
                    print('----')
            except:
                failed_follow_format_final_answer += 1
                print(answer, gt)
                print('----')
                continue
            
            
        

        total_iou += iou
        
    print("The number of failed to follow the format (question, final answer): ", failed_follow_format_question, failed_follow_format_final_answer)
    print(total_acc, len(questions)-failed_follow_format_question-failed_follow_format_final_answer)
    print("Accuracy: ", total_acc/(len(questions)-failed_follow_format_question-failed_follow_format_final_answer))

    print("Accuracy MMLU: ", total_acc_mmlu/len(questions))
    # %%
    # print(avg_grounding_question/len(questions))
    # print(avg_grounding_answer/len(questions))
    # %%
    print(avg_len_grounding_question/len(questions))
    print(avg_len_grounding_answer/len(questions))

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--llm_model', type=str, default='gemini', help='The language model to query', choices=['gemini-1.5-pro-002', 'gemini-1.5-flash-002', 'claude', 'gpt-4o-2024-08-06', 'gpt-4o-mini-2024-07-18', 'llama_transformer', 'llama_groq'])
    arg_parser.add_argument('--dataset', type=str, default='GSM8K', help='The dataset to query', choices=['GSM8K', 'StrategyQA', 'p_GSM8K', 'AQUA', 'MultiArith', 'ASDiv', 'SVAMP', 'commonsenseQA', 'date', 'sports', 'reclor', 'CLUTRR'])
    arg_parser.add_argument('--prompt_used', type=str, default='fs_inst', help='The prompt used to query the language model', choices=['zs', 'fs', 'fs_inst'])
    arg_parser.add_argument('--answer_mode', type=str, default='design_1_v4', help='The answer mode', choices=['da', 'cot', 'design_1_v4'])
    arg_parser.add_argument('--save_answer', action='store_true')
    arg_parser.add_argument('--data_mode', type=str, default='longest', help='The data mode', choices=['random', 'longest'])
    args = arg_parser.parse_args()
    
    prompt_design = 'design_1'
    version = 'v4'
    
    # data path
    if args.dataset == 'p_GSM8K':
        data_path = f'../data/p_GSM8K/r-gsm.jsonl'
    else:
        data_path = f'../data/{args.dataset}/test.jsonl'    
    
    if args.data_mode == 'random':
        df_path = f'../results/{args.dataset}/{args.answer_mode}/fs_inst_{args.llm_model}_temp_0_random.csv'
    else:
        df_path = f'../results/{args.dataset}/{args.answer_mode}/fs_inst_{args.llm_model}_temp_0.csv'


    if args.prompt_used in ['fs', 'fs_inst']:
        prefix = 'The answer is'
        prefix = 'The answer is'
    elif args.prompt_used == 'zs':
        prefix = 'Final answer:'
        
    
    # read data
    data = read_jsonl_file(data_path)
    # read df
    df = pd.read_csv(df_path)
    questions = df['question'].tolist()
    answers = df['answer'].tolist()
    ids = df['id'].tolist()

    print(len(df))
    #
    # test_df = pd.read_csv(f"/Users/tinnguyen/Downloads/LAB_PROJECTS/textual_grounding/results/{args.dataset}/design_1_v4/fs_inst_gemini_temp_0.csv")
    # test_ids = test_df['id'].tolist()
    # # extract ids in test_ids for df
    # df = df[df['id'].isin(test_ids)]

    # questions = df['question'].tolist()
    # answers = df['answer'].tolist()
    # ids = df['id'].tolist()

    # print(len(df), len(test_df))
    # %%
    # read gt
    gts = []
    for id in ids:
        for temp in data:
            if args.dataset == 'p_GSM8K':
                if temp['index'] == id:
                    gt = temp['answer']
                    gts.append(float(gt))
            elif args.dataset == 'commonsenseQA':
                if temp['id'] == id:
                    gt = temp['answerKey']
                    gts.append(gt)
            else:
                if temp['id'] == id:
                    gt = temp['answer']
                    if args.dataset in ['GSM8K', 'MultiArith', "SVAMP"]:
                        gt = gt.split('####')[1].strip()
                        if ',' in gt:
                            gt = gt.replace(',', '')
                        gts.append(float(gt))
                    if args.dataset == 'date':
                        gt = gt.split('####')[1].strip()
                        gts.append(gt)
                    if args.dataset == 'ASDiv':
                        #if gt is list, convert it to string
                        if type(gt) == list:
                            gt = gt[0]
                        gt = gt.replace(',', '')
                        gts.append(float(gt))
                    if args.dataset in ['StrategyQA', 'sports']:
                        gts.append(gt)
                    if args.dataset == 'AQUA':
                        gts.append(gt)
                    
    compute_acc(questions, answers, gts, args.dataset, prefix)