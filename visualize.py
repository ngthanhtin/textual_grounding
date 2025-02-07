from arg_parser import get_common_args

import yaml, os
import pandas as pd
from utils.utils import add_color_to_tags, add_color_to_tags_2, extract_parts_1, read_jsonl_file, count_tags

from utils.mmlu import check_math_answer, check_aqua_answer, check_asdiv_answer, check_bool_answer, check_exact_match_answer, compute_acc_gsm_plus, check_multiple_choice_answer, check_gsm_hard_answer, check_drop_answer, check_squad_answer

from load_dataset import DatasetLoader

def create_cot_highlight_html(dataset, questions, answers, gts, check_correct=False):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Question and Answer Highlights</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            .highlight {
                background-color: #FFFF00; /* Yellow background for visibility */
                font-weight: bold; /* Bold text for emphasis */
            }
            .container {
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }
            .question, .answer {
                flex: 1;
                padding: 10px;
            }
        </style>
    </head>
    <body>
    """
    
    if check_correct == True:
        correct_value = 1
    else:
        correct_value = 0
        
    for i, (question, answer, gt) in enumerate(zip(questions, answers, gts)):
        if dataset == 'ASDiv':
            acc = check_asdiv_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['GSM8K', 'p_GSM8K', 'MultiArith', 'SVAMP', 'GSM8K_Hard', 'GSM_Plus']:
            acc = check_math_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['drop_break', 'drop_cencus']:
            acc = check_drop_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['AQUA']:
            acc = check_aqua_answer(question, answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['StrategyQA', 'navigate', 'causal_judgement', 'web_of_lies']:
            acc = check_bool_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['date', 'wikimultihopQA']:
            acc = check_exact_match_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['squad']:
            acc = check_squad_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['logical_deduction_three_objects', 'logical_deduction_five_objects', 'logical_deduction_seven_objects', 'reasoning_about_colored_objects', 'commonsenseQA', 'spartQA', 'tracking_shuffled_objects_seven_objects']:
            acc = check_multiple_choice_answer(question, answer, gt)
            if acc != correct_value:
                continue
        html_content += f"<div class='container'>"
        # html_content += f"<div class='question'><strong>Question:</strong> {question}</div>"
        html_content += f"<div class='answer'><strong>{i}/ Question:</strong> {question}<br><br><strong>Answer:</strong>{answer}<br>GT: {gt}</div>"
        html_content += "</div>\n"

    # Close the HTML tags
    html_content += """
    </body>
    </html>
    """

    return html_content

def create_highlight_html(dataset, questions, answers, gts, check_correct=False):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Question and Answer Highlights</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            .highlight {
                background-color: #FFFF00; /* Yellow background for visibility */
                font-weight: bold; /* Bold text for emphasis */
            }
            .container {
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }
            .question, .answer {
                flex: 1;
                padding: 10px;
            }
        </style>
    </head>
    <body>
    """
    if check_correct == True:
        correct_value = 1
    else:
        correct_value = 0
    
    tag_in_both_qa = 0
    num_tags_in_question = 0
    num_tags_in_answer = 0
    
    save_infos = []
    fully_repeat = 0
    for i, (question, answer, gt) in enumerate(zip(questions, answers, gts)):
        
        try:
            reformulated_question, extracted_answer = extract_parts_1(answer)
            num_tags_in_answer += count_tags(extracted_answer)
            num_tags_in_question += count_tags(reformulated_question)
            import re
            repeat_question = re.sub(r'</?fact\d+>', '', reformulated_question) # remove tags
            if repeat_question.strip() == question.strip():
                fully_repeat += 1
            if '<fact' in reformulated_question and '<fact' in extracted_answer:
                tag_in_both_qa += 1
        except:
            # num_tags_in_answer += count_tags(answer)
            # num_tags_in_question += count_tags(answer)
            print("Can not extract parts...")
            continue
        
        if dataset == 'ASDiv':
            acc = check_asdiv_answer(answer, gt)
            if acc != correct_value:
                continue
        
        if dataset in ['GSM8K', 'GSM_Symbolic', 'p_GSM8K', 'MultiArith', 'SVAMP', 'GSM8K_Hard', 'GSM_Plus']:
            acc = check_math_answer(answer, gt)
            if acc != correct_value:
                continue
            save_infos.append((i, question, answer, gt))
            
        if dataset in ['drop_break', 'drop_cencus']:
            acc = check_drop_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['AQUA']:
            acc = check_aqua_answer(question, answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['StrategyQA', 'navigate', 'causal_judgement', 'web_of_lies']:
            acc = check_bool_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['date', 'wikimultihopQA']:
            acc = check_exact_match_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['squad']:
            acc = check_squad_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['logical_deduction_three_objects', 'logical_deduction_five_objects', 'logical_deduction_seven_objects', 'reasoning_about_colored_objects', 'commonsenseQA', 'spartQA', 'tracking_shuffled_objects_seven_objects']:
            acc = check_multiple_choice_answer(question, answer, gt)
            if acc != correct_value:
                continue
            
        highlighted_answer = add_color_to_tags(extracted_answer)
        highlighted_question = add_color_to_tags(reformulated_question)
        # highlighted_answer = extracted_answer
        # highlighted_question = reformulated_question
        
        html_content += f"<div class='container'>"
        # html_content += f"<div class='question'><strong>Question:</strong> {question}</div>"
        html_content += f"<div class='answer'><strong>{i}/ Reformatted Question:</strong> {highlighted_question}<br><br><strong>Answer:</strong>{highlighted_answer}<br><br><strong>GT:</strong>{gt}</div>"
        html_content += "</div>\n"

    print(f"Tag in both QA: {tag_in_both_qa/len(questions)}")
    print(f"Num tags in question: {num_tags_in_question/len(questions)}")
    print(f"Num tags in answer: {num_tags_in_answer/len(questions)}")
    print(f"Fully repeat: {fully_repeat/len(questions)}")
    # Close the HTML tags
    html_content += """
    </body>
    </html>
    """

    # save save_infos to a df
    # df = pd.DataFrame(save_infos, columns=['id', 'question', 'answer', 'gt'])
    # print(len(df))
    # df.to_csv(f'save_infos_{check_correct}.csv', index=False)
    return html_content

if __name__ == "__main__":
    arg_parser = get_common_args()
    arg_parser.add_argument('--save_html', action='store_true')
    arg_parser.add_argument('--check_correct', action='store_true')
    args = arg_parser.parse_args()
    
    args.data_mode = 'longest'
    # args.data_mode = 'full'
    
    args.answer_mode = 'design_1_v4'

    # args.data_mode = 'full'
    tail = f'_temp_10_{args.data_mode}'
    result_folder = f"results_auto_tagging"
    # result_folder = f"results_qwen_without_system_prompt"
    # result_folder = f"results_qwen"
    # result_folder = 'results_auto_tagging'
    # result_folder = 'results_auto_tagging_random_tag'
    
    save_html_path = f"{result_folder}/{args.dataset}/{args.answer_mode}/highlights_{args.prompt_used}_{args.llm_model}{tail}.html"
    df_path = f'{result_folder}/{args.dataset}/{args.answer_mode}/{args.prompt_used}_{args.llm_model}{tail}.csv'
    
    if args.answer_mode == 'grounding_cot':
        if args.check_correct == True:
            save_html_path = f"{result_folder}/{args.dataset}/design_1_v4/highlights_{args.prompt_used}_{args.llm_model}{tail}_correct.html"
        else:
            save_html_path = f"{result_folder}/{args.dataset}/design_1_v4/highlights_{args.prompt_used}_{args.llm_model}{tail}_wrong.html"
        df_path = f'{result_folder}/{args.dataset}/design_1_v4/{args.prompt_used}_{args.llm_model}{tail}.csv'
    else:
        if args.check_correct == True:
            save_html_path = f"{result_folder}/{args.dataset}/{args.answer_mode}/highlights_{args.prompt_used}_{args.llm_model}{tail}_correct.html"
        else:
            save_html_path = f"{result_folder}/{args.dataset}/{args.answer_mode}/highlights_{args.prompt_used}_{args.llm_model}{tail}_wrong.html"
        
    if not os.path.exists(df_path):
        df_path = df_path.replace('longest', 'shortest')
        if not os.path.exists(df_path):
            df_path = df_path.replace('shortest', 'full')
        
    df = pd.read_csv(df_path)
    questions = df['question'].tolist()
    answers = df['answer'].tolist()
    ids = df['id'].tolist()
    
    # load gt
   # load config file
    # data_path & fewshot_prompt_path & max_question_length
    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    base_data_path = args.base_data_path
    gt_data_path = os.path.join(base_data_path, config['data_paths'][args.dataset])
    
    dataloader = DatasetLoader(config_path='configs/config.yaml', base_data_path=args.base_data_path, base_few_shot_prompt_path=args.base_prompt_path, dataset=args.dataset, data_mode=args.data_mode, num_samples=args.num_samples)
    
    print(f"Loading data from {gt_data_path}...")
    gts = dataloader.retrieve_gts(ids)
    
    if args.answer_mode == 'cot':
        html_content = create_cot_highlight_html(args.dataset, questions, answers, gts, check_correct=args.check_correct)
    else:
        html_content = create_highlight_html(args.dataset, questions, answers, gts, check_correct=args.check_correct)    
    
    if args.save_html:
        print(save_html_path)
        # Optionally write to an HTML file
        with open(save_html_path, "w") as file:
            file.write(html_content)