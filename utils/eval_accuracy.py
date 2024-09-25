# %%
import pandas as pd
from utils import extract_parts_1, calculate_iou, add_color_to_tags, extract_conclusion, extract_parts_only_answer, check_for_word, read_jsonl_file

llm_model = 'claude'
dataset = 'ASDiv' # 'GSM8K', 'StrategyQA'
prompt_used = 1 #0, 1, 2
if dataset == 'p_GSM8K':
    data_path = f'../data/{dataset}/r-gsm.jsonl'
else:
    data_path = f'../data/{dataset}/test.jsonl'    
df_path = f'../results/{dataset}/design_1_v4/fs_inst_{llm_model}.csv'

if prompt_used in [0,1]:
    prefix = 'The answer is'
    prefix = 'The answer is'
elif prompt_used == 2:
    prefix = 'Final answer:'

# %%
# read data
data = read_jsonl_file(data_path)
# read df
df = pd.read_csv(df_path)
questions = df['question'].tolist()
answers = df['answer'].tolist()
ids = df['id'].tolist()
# read gt
gts = []
for id in ids:
    for temp in data:
        if dataset == 'p_GSM8K':
            if temp['index'] == id:
                gt = temp['answer']
                gts.append(float(gt))
        else:
            if temp['id'] == id:
                gt = temp['answer']
                if dataset in ['GSM8K', 'MultiArith']:
                    gt = gt.split('####')[1].strip()
                    if ',' in gt:
                        gt = gt.replace(',', '')
                if dataset == 'ASDiv':
                    #if gt is list, convert it to string
                    if type(gt) == list:
                        gt = gt[0]
                    gt = gt.replace(',', '')
                gts.append(float(gt))
        


# %%
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
    try:
        reformulated_question, extracted_answer = extract_parts_1(answer)
        # extracted_answer = extract_parts_only_answer(answer)
        # reformulated_question = ''
    except:
        failed_follow_format_question += 1
        continue
    iou, question_tags, answer_tags = calculate_iou(reformulated_question, extracted_answer)
    
    if len(question_tags) == 0:
        failed_follow_format_question += 1
        continue
    if len(answer_tags) == 0:
        print('here')
        failed_follow_format_final_answer += 1
        continue
        
    len_question_tag, len_answer_tag = len(question_tags), len(answer_tags)
    avg_grounding_question+=len_question_tag
    avg_grounding_answer+=len_answer_tag
    
    total_tag_question_legth = 0
    for tag in question_tags:
        total_tag_question_legth+= len(tag[1])
    avg_len_grounding_question+=total_tag_question_legth/len(question_tags)
    
    total_tag_answer_legth = 0
    for tag in answer_tags:
        total_tag_answer_legth+= len(tag[1])
    avg_len_grounding_answer+=total_tag_answer_legth/len(answer_tags)
    
    if dataset in ['GSM8K', 'p_GSM8K', 'MultiArith', 'ASDiv']:
        answer = answer.replace("*", "").replace("$", "")
        # conclusion = extract_conclusion(answer.lower(), prefix.lower())   
        # conclusion = conclusion.replace(f'{prefix.lower()}', '')
        # the answer is inside {}
        try:
            conclusion = answer.split('{')[1].split('}')[0]
            print(conclusion, gt)
        except:
            failed_follow_format_final_answer += 1
            continue
        
        conclusion = conclusion.strip()
        if conclusion[-1] == '.':
            conclusion = conclusion[:-1]
        
        try:
            if ',' in conclusion:
                conclusion = conclusion.replace(',', '')
            if '$' in conclusion:
                conclusion = conclusion.replace('$', '')
                
            if float(conclusion) == gt:
                total_acc += 1
        except:
            failed_follow_format_final_answer += 1
            continue
    elif dataset == 'StrategyQA':
        # if check_for_word(answer, '1'):
        #     bool_extracted_answer = True
        # else:
        #     bool_extracted_answer = False

        conclusion = extract_conclusion(answer.lower(), prefix.lower())   
        conclusion = conclusion.replace(f'{prefix.lower()}', '')
        
        conclusion = conclusion.strip()
        if conclusion[-1] == '.':
            conclusion = conclusion[:-1]
            if conclusion == '1':
                bool_extracted_answer = True
            else:
                bool_extracted_answer = False
        if bool_extracted_answer == bool(gt):
            total_acc += 1

    total_iou += iou
    
print("The number of failed to follow the format (question, final answer): ", failed_follow_format_question, failed_follow_format_final_answer)
print(total_acc, len(questions)-failed_follow_format_question-failed_follow_format_final_answer)
print("Accuracy: ", total_acc/(len(questions)-failed_follow_format_question-failed_follow_format_final_answer))
# %%
print(avg_grounding_question/len(questions))
print(avg_grounding_answer/len(questions))
# %%
print(avg_len_grounding_question/len(questions))
print(avg_len_grounding_answer/len(questions))
# %%
