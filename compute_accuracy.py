# if args.dataset == 'GSM8K':
        #extract the answer
        # gts = [x.split("####")[-1].strip() for x in gts] 
        
        
# %%
import pandas as pd
from utils.utils import extract_parts, calculate_iou, add_color_to_tags, extract_conclusion, extract_parts_only_answer, check_for_word

llm_model = 'gemini'
dataset = 'StrategyQA' # 'GSM8K', 'StrategyQA'
prompt_used = 2 #0, 1, 2
save_html_path = f"results/{dataset}/design_1_50/question_answer_highlights_prompt_{prompt_used}_{llm_model}.html"
df_path = f'results/{dataset}/design_1_50/test_grounding_answer_prompt_{prompt_used}_{llm_model}.csv'
gt_path = f'sample_datasets/{dataset}/gt_50.txt'
if prompt_used in [0,1]:
    prefix = 'The answer is'
    prefix = 'The answer is'
elif prompt_used == 2:
    prefix = 'Final answer:'

# read gt
with open(gt_path, 'r') as file:
    gts = file.readlines()
    gts = [x.strip() for x in gts]
    if dataset == 'GSM8K':
        gts = [float(x.replace(',','')) for x in gts] # GSM8K
    elif dataset == 'StrategyQA':
        gts = [bool(x) for x in gts]
# %%
df = pd.read_csv(df_path)
questions = df['question'].tolist()
answers = df['answer'].tolist()
# %%
# Append each question and its highlighted answer to the HTML content
total_iou = 0
total_acc = 0
avg_grounding_question = 0
avg_grounding_answer = 0
failed_follow_format_question = 0
failed_follow_format_final_answer = 0

for i, (question, answer, gt) in enumerate(zip(questions, answers, gts)):
    try:
        reformulated_question, extracted_answer = extract_parts(answer)
        # extracted_answer = extract_parts_only_answer(answer)
        # reformulated_question = ''
    except:
        failed_follow_format_question += 1
        continue
    iou, len_question_tag, len_answer_tag = calculate_iou(reformulated_question, extracted_answer)
    
    avg_grounding_question+=len_question_tag
    avg_grounding_answer+=len_answer_tag
    
    if dataset == 'GSM8K':
        answer = answer.replace("*", "").replace("$", "")
        conclusion = extract_conclusion(answer.lower(), prefix.lower())   
        conclusion = conclusion.replace(f'{prefix.lower()}', '')
        
        conclusion = conclusion.strip()
        if conclusion[-1] == '.':
            conclusion = conclusion[:-1]
        
        try:
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
print(total_iou/len(questions))
print(total_acc/len(questions))