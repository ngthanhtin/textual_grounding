# %% # check examples where grounding is correct but DA and COT are wrong
import pandas as pd
from utils.utils import read_jsonl_file

llm_model = 'claude'
dataset = 'ASDiv' # 'GSM8K', 'StrategyQA'

if dataset == 'p_GSM8K':
    data_path = f'data/{dataset}/r-gsm.jsonl'    
else:
    data_path = f'data/{dataset}/test.jsonl'

df_da_path = f'results/{dataset}/da/fs_inst_{llm_model}.csv'
df_cot_path = f'results/{dataset}/cot/fs_inst_{llm_model}.csv'
df_grounding_path = f'results/{dataset}/design_1_v4/fs_inst_{llm_model}.csv'

def read_df(df_path):
    df = pd.read_csv(df_path)
    questions = df['question'].tolist()
    answers = df['answer'].tolist()
    ids = df['id'].tolist()
    return questions, answers, ids

def extract_answer(answer):
    try:
        answer = answer.split('{')[1].split('}')[0].lower()
        
        if ',' in answer:
            answer = answer.replace(',', '')
        if '$' in answer:
            ansewr = answer.replace('$', '')
        if '.' == answer[-1]:
            answer = answer[:-1]
        return answer
    except:
        return None

df_da, df_cot, df_grounding = read_df(df_da_path), read_df(df_cot_path), read_df(df_grounding_path)
questions_da, answers_da, ids_da = df_da
questions_cot, answers_cot, ids_cot = df_cot
questions_grounding, answers_grounding, ids_grounding = df_grounding

# %%
# read data
data = read_jsonl_file(data_path)

# read gt
gts = []
for id in ids_grounding:
    for temp in data:
        if temp['id'] == id:
            gt = temp['answer']
            if dataset in ['GSM8K', 'p_GSM8K', 'MultiArith']:
                gt = gt.split('####')[1].strip()
                if ',' in gt:
                    gt = gt.replace(',', '')
            if dataset == 'ASDiv':
                #if gt is list, convert it to string
                if type(gt) == list:
                    gt = gt[0]
                gt = gt.replace(',', '')
            gts.append(float(gt))

compares = []
for i, (id, gt) in enumerate(zip(ids_grounding, gts)):
    grounding_answer = extract_answer(answers_grounding[i])
    if grounding_answer is None:
        print("Grounding: ", grounding_answer)
        continue
    # find id in df_cot
    index_in_cot = ids_cot.index(id)
    # cot_answer = extract_answer(answers_cot[index_in_cot])
    try:
        cot_answer = answers_cot[index_in_cot].split('Answer')[1].strip()
    except:
        continue
    # extract only numbers in the answer
    # cot_answer = ''.join(filter(str.isdigit, cot_answer))
    
    cot_answer = cot_answer.replace(":", "").replace("*", "").replace("$", "").replace(",", "").replace("{", "").replace("}", "")
    if '.' in cot_answer[-1]:
        cot_answer = cot_answer[:-1]
    cot_answer = cot_answer.strip()
    if cot_answer is None:
        print("CoT: ", cot_answer)
        continue
    # # find id in df_da
    # index_in_da = ids_da.index(id)
    # da_answer = extract_answer(answers_da[index_in_da])
    # if da_answer is None:
    #     da_answer = answers_da[index_in_da].split('Answer:')[1].strip()
    #     if '.' in da_answer:
    #         da_answer = da_answer.split('.')[0]
    #     if "{" in da_answer:
    #         da_answer = da_answer.replace('{', '').replace('}', '').strip()
    #     if da_answer == '':
    #         print("DA: ", da_answer)
    #         continue
    
    # if float(grounding_answer) == gt and float(cot_answer) != gt and float(da_answer) != gt:
    try:
        if float(grounding_answer) == float(gt) and float(cot_answer) != float(gt):
            compares.append([questions_grounding[i], answers_grounding[i], answers_cot[index_in_cot], gt])
            # print(questions_grounding[i])
            # print('----------------')
            # print(answers_grounding[i])
            # print('----------------')
            # print(answers_cot[index_in_cot])
            # print(grounding_answer, cot_answer, gt)
            print(question_grounding[i])
            print('----------------')
    except:
        continue
        
# %%
# Sample data: lists of Grounding CoT and CoT responses
grounding_responses, cot_responses = [], []
print(len(compares))
for i in range(4):
    grounding_responses.append(compares[i][1])
    cot_responses.append(compares[i][2])

import re
# Predefined colors for each fact tag
tag_colors = {
    'fact1': '#ff9999',  # light red
    'fact2': '#99ccff',  # light blue
    'fact3': '#99ff99',  # light green
    'fact4': '#ffcc99',  # light orange
    'fact5': '#ccccff',  # light purple
}

# Function to highlight tags in the Grounding CoT response with different colors
def highlight_tags(response):
    def replace_tag(match):
        tag = match.group(1)  # e.g., fact1, fact2, etc.
        content = match.group(2)  # The content inside the tag
        color = tag_colors.get(tag, '#ffffff')  # Default to white background if no color is set
        return f'<span style="background-color: {color}">{content}</span>'
    
    # Use regex to find and replace tags with different colors
    highlighted_response = re.sub(r'<(fact\d+)>(.*?)<\/\1>', replace_tag, response)
    return highlighted_response

# Function to generate HTML content
def generate_html(grounding_responses, cot_responses):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Grounding CoT vs CoT Comparison</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            /* Styling for highlighted tags */
            span {
                font-weight: bold;
                padding: 3px;
            }
        </style>
    </head>
    <body>

        <h2>Grounding CoT vs CoT Comparison</h2>
        <table>
            <tr>
                <th>Grounding CoT Response</th>
                <th>CoT Response</th>
            </tr>
    """
    
    # Loop through each pair of Grounding CoT and CoT responses
    for grounding, cot in zip(grounding_responses, cot_responses):
        highlighted_grounding = highlight_tags(grounding)
        
        highlighted_grounding_answer = highlighted_grounding.split('Answer:')[1].strip()
        highlighted_grounding_question = highlighted_grounding.split('Answer:')[0].strip()
        
        html_content += f"""
        <tr>
            <td><b>Question: </b>{highlighted_grounding_question}<br><b>Answer: </b>{highlighted_grounding_answer}</td>
            <td><b>Answer: </b>{cot}</td>
        </tr>
        """

    # Closing the table and HTML structure
    html_content += """
        </table>
    </body>
    </html>
    """
    
    return html_content

# Generate the HTML file
html_output = generate_html(grounding_responses, cot_responses)

# Write the HTML content to a file
with open('cot_comparison_highlighted_asdiv.html', 'w') as file:
    file.write(html_output)
# %%
