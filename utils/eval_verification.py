# %%
import openai
import anthropic
import pandas as pd
from collections import defaultdict
from utils import extract_parts_1
import re
from keys import API_KEYS
from utils import read_jsonl_file
from tqdm import tqdm
# %%
def remove_html_tags(text):
    # This regex matches all HTML tags
    clean_text = re.sub(r'<.*?>', '', text)
    return clean_text

def extract_tagged_phrases(text):
    # Defaultdict to hold lists of phrases for each tag
    pattern = re.compile(r"<([a-z])>(.*?)<\/[a-z]>")
    
    # Initialize a dictionary where each key is a tag and the value is a list of phrases
    tagged_phrases = defaultdict(list)
    
    # Find all tags and their corresponding phrases
    for tag, phrase in pattern.findall(text):
        tagged_phrases[tag].append(phrase)
    
    return dict(tagged_phrases)

# %%
# Function to send a query to GPT-4o for evaluating citation recall
def evaluate_verification_llm(question, answer, gt):
    """
    question and answer that have no tags
    """
    prompt = """
    You are given a model-generated text and a ground truth reference. Your task is to assess whether the final answer from the model matches the ground truth, focusing on semantic content, thematic alignment, and intent rather than exact wording. Recognize and accept synonyms, paraphrasing, or stylistic differences, as long as they convey the same meaning as the ground truth.\n\
    Question: {question}\n\
    Model-generated Answer: {answer}\n\
    Ground Truth: {gt}\n\
    
    After analysis, report whether the model's answer aligns with the ground truth by responding with either "Yes" or "No". Additionally, provide feedback on any discrepancies or areas of alignment, and suggest improvements if necessary.\n\
         
    Please provide the final answer in the format: {Yes} or {No}.
    """

    # response = openai.Completion.create(
    #     engine="gpt-4o",
    #     prompt=prompt,
    #     max_tokens=10,
    #     temperature=0
    # )
    # return float(response.choices[0].text.strip())
    
    client = anthropic.Anthropic(api_key=API_KEYS['claude'])

    response = client.messages.create(
    model="claude-3-5-sonnet-20240620",
    max_tokens=1024,
    temperature=0.0,
    messages=[
    {
    "role": "user",
    "content": f"{prompt}"
    }
    ]
    )

    # extract rating
    response = response.content[0].text.strip()
    try:
        answer = response.split('{')[1].split('}')[0].lower()
    except:
        return response, 'not sure'
    
    try:
        if answer == 'yes' or answer == "1":
            answer = True
        elif answer == 'no' or answer == "0":
            answer = False
    except:
        response = 'not sure'
    return response, answer
    

def verify_all(questions, answers, gts):
    # # Extract tagged elements from reformatted question
    # question_tags = extract_tagged_phrases(reformatted_question)
    # # Extract tagged elements from answer
    # answer_tags = extract_tagged_phrases(answer)
    
    
    accuracy = 0
    num_not_sure = 0
    responses = []
    for question, answer, gt in tqdm(zip(questions, answers, gts)):
        reformatted_question, extracted_answer = extract_parts_1(answer)
        answer = remove_html_tags(extracted_answer)
        
        response, is_correct = evaluate_verification_llm(question, answer, gt)
        responses.append(response)
        if is_correct != 'not sure':
            accuracy += is_correct
        else:
            num_not_sure += 1
    
    accuracy /= len(questions)
    return responses, accuracy, num_not_sure

# %% read df and gt as well
import pandas as pd
llm_model = 'claude'
dataset = 'GSM8K' # 'GSM8K', 'StrategyQA'
df_path = f'../results/{dataset}/cot/fs_inst_{llm_model}.csv'
df = pd.read_csv(df_path)
questions = df['question'].tolist()
answers = df['answer'].tolist()
ids = df['id'].tolist()

if dataset == 'p_GSM8K':
    data_path = f'../data/{dataset}/r-gsm.jsonl'
else:
    data_path = f'../data/{dataset}/test.jsonl'    
# %%
# read GT
data = read_jsonl_file(data_path)
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
            if dataset == 'ASDiv':
                #if gt is list, convert it to string
                if type(gt) == list:
                    gt = gt[0]
                gt = gt.replace(',', '')
            gts.append(float(gt))
# %%
# Run evaluation
responses, accuracy, num_not_sure = verify_all(questions, answers, gts)
print(accuracy, num_not_sure)

# %%
# create a new dataframe to save the results
df = pd.DataFrame(data={'id': ids,'response': responses, 'accuracy': accuracy})
df.to_csv(f'{llm_model}_cot_ai_verification.csv', index=False)
# %%

# %%
