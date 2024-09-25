# %%
import pandas as pd
from utils import extract_parts_1, calculate_iou, add_color_to_tags, extract_conclusion, extract_parts_only_answer, check_for_word, read_jsonl_file

llm_model = 'claude'
dataset = 'ASDiv' # 'GSM8K', 'StrategyQA'
prompt_used = 'cot'
if dataset == 'p_GSM8K':
    data_path = f'../data/{dataset}/r-gsm.jsonl'    
else:
    data_path = f'../data/{dataset}/test.jsonl'

df_path = f'../results/{dataset}/{prompt_used}/fs_inst_{llm_model}.csv'


prefix = 'Answer'

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
        if temp['id'] == id:
            gt = temp['answer']
            if dataset in ['GSM8K', 'p_GSM8K', 'MultiArith']:
                gt = gt.split('####')[1].strip()
                if ',' in gt:
                    gt = gt.replace(',', '')
                # gt = gt
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
    # answer is in the format Answer: {answer}
    try:
        answer = answer.split('Answer')[1].strip()
    except:
        failed_follow_format_final_answer += 1
        print(answer)
        continue
    # extract only numbers in the answer
    # conclusion = ''.join(filter(str.isdigit, answer))
    
    if dataset in ['GSM8K', 'p_GSM8K', 'MultiArith', 'ASDiv']:
        conclusion = answer.replace(":", "").replace("*", "").replace("$", "").replace(",", "").replace("{", "").replace("}", "")
        conclusion = conclusion.strip()
        try:
            if conclusion[-1] == '.':
                conclusion = conclusion[:-1]
        except:
            failed_follow_format_final_answer += 1
            print(answer)
            continue
        
        try:    
            if float(conclusion) == gt:
                total_acc += 1
        except:
            # print(answer)
            # print('----')
            failed_follow_format_final_answer += 1
            continue
    
print("The number of failed to follow the format (question, final answer): ", failed_follow_format_question, failed_follow_format_final_answer)
# print(total_iou/len(questions))
print(total_acc, len(questions)-failed_follow_format_question-failed_follow_format_final_answer)
print("Accuracy: ", total_acc/len(questions))

# %%
