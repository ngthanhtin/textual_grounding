# %%
import pandas as pd
from utils.utils import add_color_to_tags, extract_parts_0, extract_parts_1
import argparse

def create_highlight_html(questions, answers):
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
    for i, (question, answer) in enumerate(zip(questions, answers)):
        try:
            reformulated_question, extracted_answer = extract_parts_1(answer)
        except:
            print("Can not extract parts...")
            continue
        
        highlighted_answer = add_color_to_tags(extracted_answer)
        highlighted_question = add_color_to_tags(reformulated_question)
        
        html_content += f"<div class='container'>"
        html_content += f"<div class='question'><strong>Question:</strong> {question}</div>"
        html_content += f"<div class='answer'><strong>Reformatted Question:</strong> {highlighted_question}<br><br><strong>Answer:</strong>{highlighted_answer}</div>"
        html_content += "</div>\n"

    # Close the HTML tags
    html_content += """
    </body>
    </html>
    """

    return html_content

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--llm_model', type=str, default='gemini', help='The language model to query', choices=['gemini', 'claude'])
    arg_parser.add_argument('--dataset', type=str, default='GSM8K', help='The dataset to query', choices=['GSM8K', 'StrategyQA'])
    arg_parser.add_argument('--prompt_used', type=str, default='fs_inst', help='The prompt used to query the language model', choices=['zs', 'fs', 'fs_inst'])
    arg_parser.add_argument('--save_html', action='store_true')
    
    args = arg_parser.parse_args()
    
    save_html_path = f"results/{args.dataset}/design_1_tin_v2/question_answer_highlights_prompt_{args.prompt_used}_{args.llm_model}.html"
    df_path = f'results/{args.dataset}/design_1_tin_v2/test_grounding_answer_prompt_{args.prompt_used}_{args.llm_model}.csv'

    if args.prompt_used in ["fs", "fs_inst"]:
        prefix = 'The answer is'
    elif args.prompt_used == "zs":
        prefix = 'Final answer:'

    df = pd.read_csv(df_path)
    questions = df['question'].tolist()
    answers = df['answer'].tolist()

    # create html
    html_content = create_highlight_html(questions, answers)
    
    if args.save_html:
        # Optionally write to an HTML file
        with open(save_html_path, "w") as file:
            file.write(html_content)