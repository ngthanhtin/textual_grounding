from arg_parser import get_common_args

import yaml, os
import pandas as pd
from utils.utils import add_color_to_tags, extract_parts_1, read_jsonl_file, retrieve_gts

from utils.mmlu import check_math_answer, check_aqua_answer, check_asdiv_answer, check_bool_answer, check_exact_match_answer, compute_acc_gsm_plus, check_multiple_choice_answer, check_gsm_hard_answer

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
        if dataset in ['AQUA']:
            acc = check_aqua_answer(question, answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['StrategyQA', 'navigate', 'causal_judgement', 'web_of_lies']:
            acc = check_bool_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['date', 'wikimultihopQA', 'squad']:
            acc = check_exact_match_answer(answer, gt)
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
        
    for i, (question, answer, gt) in enumerate(zip(questions, answers, gts)):
        
        try:
            reformulated_question, extracted_answer = extract_parts_1(answer)
        except:
            print("Can not extract parts...")
            continue
        
        if dataset == 'ASDiv':
            acc = check_asdiv_answer(answer, gt)
            if acc != correct_value:
                continue
        if dataset in ['GSM8K', 'p_GSM8K', 'MultiArith', 'SVAMP', 'GSM8K_Hard', 'GSM_Plus', 'drop_break', 'drop_cencus']:
            acc = check_math_answer(answer, gt)
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
        if dataset in ['date', 'wikimultihopQA', 'squad']:
            acc = check_exact_match_answer(answer, gt)
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

    # Close the HTML tags
    html_content += """
    </body>
    </html>
    """

    return html_content

if __name__ == "__main__":
    arg_parser = get_common_args()
    arg_parser.add_argument('--save_html', action='store_true')
    arg_parser.add_argument('--check_correct', action='store_true')
    args = arg_parser.parse_args()
    
    tail = '_temp_10_longest'
    # tail = '_temp_0_longest'
    result_folder = f"results_auto_tagging"
    # result_folder = f"results"
    
    # tail = '_temp_0_random'
    # result_folder = 'results'
    save_html_path = f"{result_folder}/{args.dataset}/{args.answer_mode}/highlights_{args.prompt_used}_{args.llm_model}{tail}.html"
    df_path = f'{result_folder}/{args.dataset}/{args.answer_mode}/{args.prompt_used}_{args.llm_model}{tail}.csv'
    
    if args.answer_mode == 'grounding_cot':
        if args.check_correct == True:
            save_html_path = f"{result_folder}/{args.dataset}/design_1_v4/highlights_{args.prompt_used}_{args.llm_model}{tail}_correct.html"
        else:
            save_html_path = f"{result_folder}/{args.dataset}/design_1_v4/highlights_{args.prompt_used}_{args.llm_model}{tail}_wrong.html"
        df_path = f'{result_folder}/{args.dataset}/design_1_v4/{args.prompt_used}_{args.llm_model}{tail}.csv'

    if args.prompt_used in ["fs", "fs_inst"]:
        prefix = 'The answer is'
    elif args.prompt_used == "zs":
        prefix = 'Final answer:'

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
    
    print(f"Loading data from {gt_data_path}...")
    gts = retrieve_gts(gt_data_path, ids, args.dataset)

    if args.answer_mode == 'cot':
        html_content = create_cot_highlight_html(args.dataset, questions, answers, gts, check_correct=args.check_correct)
    else:
        html_content = create_highlight_html(args.dataset, questions, answers, gts, check_correct=args.check_correct)    
    
    if args.save_html:
        # Optionally write to an HTML file
        with open(save_html_path, "w") as file:
            file.write(html_content)