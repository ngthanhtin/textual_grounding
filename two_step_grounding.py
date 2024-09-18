import google.generativeai as genai
import os
from utils.keys import API_KEYS
from google.generativeai.types import RequestOptions
from google.api_core import retry
import anthropic

import random, json, argparse
from tqdm import tqdm
import pandas as pd
from utils.utils import read_jsonl_file
random.seed(0)


from tqdm import tqdm

from tqdm import tqdm

def two_step_query_llm(llm_model, ids, questions, few_shot_prompt, prompt_used):
    formatted_phrases_list = []
        
    # Step 1: Identify and format important phrases in the question
    for id, q in tqdm(zip(ids, questions)):
        extract_prompt = f"Identify and list key phrases from the following question that are crucial to providing a comprehensive answer, format each with an single index in square bracket at the end of each phrase.\n{q}" # 1st try

        # extract_prompt = f"Identify and list key phrases from the following question {q}\n The output format is as follow:\n \
        #     [Your 1st key phrase here], [Your 1st index here]\n \
        #     [Your 2nd key phrase here], [Your 2nd index here]\n \
        #     [Your 3rd key phrase here], [Your 3rd index here]\n \
        #             ...\n \
        #     [Your Nth key phrase here], [Your Nth index here]\n \
        #     Provide the answer in aforementioned format, and nothing else" # 2nd try
        
        # extract_prompt = f"{few_shot_prompt}\n{q}" # 3rd try
        # extract_prompt = f"{few_shot_prompt}\n{q}\nPlease analyze the question and identify the key phrases crucial for answering the question. List each phrase clearly and append an index in one square bracket at the end of each phrase in ascending order. For example, if the phrase is 'The sky is blue', you should format it as 'The sky is blue [1]'."

        # extract_prompt = f"Identify and list key phrases from the following question, format each with a distinct tag e.g. <a>, <b>, <c>, etc\n{q}" # 5th try
        
        if llm_model == 'gemini':
            genai.configure(api_key=API_KEYS['gemini'])
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            try:
                response = model.generate_content(extract_prompt, request_options=RequestOptions(retry=retry.Retry(initial=10, multiplier=2, maximum=60, timeout=60)))
                phrases = response.text.split('\n')
                formatted_phrases = "\n".join([f"{phrase}" for i, phrase in enumerate(phrases)])
                formatted_phrases_list.append(formatted_phrases)
                print(formatted_phrases)
            except:
                continue
            
        elif llm_model == 'claude':
            client = anthropic.Anthropic(api_key=API_KEYS['claude'])
            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": extract_prompt}]
                )
                phrases = response.content[0].text.split('\n')
                formatted_phrases = "\n".join([f"{phrase}" for i, phrase in enumerate(phrases)])
                formatted_phrases_list.append(formatted_phrases)
            except:
                continue

    # Step 2: Generate the answer with references to the important phrases
    answers = []
    ids_can_be_answered = []
    questions_can_be_answered = []
    formatted_phrases_can_be_answered = []
    
    for id, q, formatted_phrases in tqdm(zip(ids, questions, formatted_phrases_list)):
        # answer_prompt = f"{few_shot_prompt}\nQuestion: {q}\nUse the following indexed phrases to construct your answer: {formatted_phrases}\nAnswer the question but your explanation should contain references referring back to the indexed phrases, e.g., <s>...<cite>phrase3</cite></s>."
        # answer_prompt = f"Question: {q}\nUse the following indexed phrases to construct your answer: {formatted_phrases}\nAnswer the question but your explanation should contain references referring back to the indexed phrases" + "e.g., <s>{phrase}<cite>{index}</cite></s>."  # 1st try
        
        # answer_prompt = f"{few_shot_prompt}\n{q}\n{formatted_phrases}"
        answer_prompt = f"{few_shot_prompt}\n{q}\n{formatted_phrases}\nUse the indexed phrases to construct your answer. It means that answer the question but your explanation should contain references referring back to the indexed phrases" + "e.g., <s>{[index]} {phrase}</s>."

        if llm_model == 'gemini':
            try:
                response = model.generate_content(answer_prompt, request_options=RequestOptions(retry=retry.Retry(initial=10, multiplier=2, maximum=60, timeout=60)))
                answers.append(response.text)
                questions_can_be_answered.append(q)
                ids_can_be_answered.append(id)
                formatted_phrases_can_be_answered.append(formatted_phrases)
            except:
                continue
            
        elif llm_model == 'claude':
            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": answer_prompt}]
                )
                answers.append(response.content[0].text)
                questions_can_be_answered.append(q)
                ids_can_be_answered.append(id)
                formatted_phrases_can_be_answered.append(formatted_phrases)
            except:
                continue

    return ids_can_be_answered, questions_can_be_answered, formatted_phrases_can_be_answered, answers

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--llm_model', type=str, default='gemini', help='The language model to query', choices=['gemini', 'claude'])
    arg_parser.add_argument('--dataset', type=str, default='GSM8K', help='The dataset to query', choices=['GSM8K', 'StrategyQA'])
    arg_parser.add_argument('--prompt_used', type=str, default='fs_inst', help='The prompt used to query the language model', choices=['zs', 'fs', 'fs_inst'])
    arg_parser.add_argument('--save_answer', action='store_true')
    
    args = arg_parser.parse_args()
    
    data_path = f'data/{args.dataset}/test.jsonl'
    fewshot_prompt_path = f"prompt/{args.dataset}/fewshot_grounding_from_key_phrases_v2.txt"
    
    save_folder = f'results/{args.dataset}/design_1_2step_grounding_v2/'
    os.makedirs(save_folder, exist_ok=True)
    save_path = f'{save_folder}/test_2step_grounding_answer_prompt_{args.prompt_used}_{args.llm_model}.csv'
    
    
    # read file grounding_prompt.txt
    with open(fewshot_prompt_path, 'r') as file:
        few_shot_prompt = file.read()
        
    # read data
    data = read_jsonl_file(data_path)
    # take random data
    random_data = random.sample(data, 10)
    
    questions = [x["question"] for x in random_data]
    ids = [x["id"] for x in random_data]       
            
    ids_can_be_answered, questions_can_be_answered, formatted_phrases_can_be_answered, answers = two_step_query_llm(args.llm_model, ids, questions, few_shot_prompt, args.prompt_used)
    
    if args.save_answer:
        # save answers and questions to csv file (the len of question and answer should be the same)
        df = pd.DataFrame({'id': ids_can_be_answered, 'question': questions_can_be_answered, 'Formatted Phrases': formatted_phrases_can_be_answered, 'answer': answers})
        df.to_csv(save_path, index=False)