import google.generativeai as genai
import os
from utils.keys import API_KEYS
from google.generativeai.types import RequestOptions
from google.api_core import retry
import anthropic

import random, json, argparse
from tqdm import tqdm
import pandas as pd
from utils.utils import read_jsonl_file, extract_last_sentence
random.seed(0)


def query_llm(llm_model, ids, questions, few_shot_prompt, prompt_used, answer_mode='da'):
    answers = []
    ids_can_be_answered = []
    questions_can_be_answered = []
    
    for id, q in tqdm(zip(ids, questions)):
        # prompt = f"{few_shot_prompt}\n{q}" # prompt 0
        # prompt = f"{few_shot_prompt}\n{q}\nCan you help me answer the question and use <a></a> tags to highlight important information and its reference to the information in the question by using <ref></ref> tags." # prompt 1
        # prompt = f"{q}\nCan you help me answer the question and use <a></a> tags to highlight important information and its reference to the information in the question by using <ref></ref> tags." # prompt zeroshot
        
        last_sentence = extract_last_sentence(q)
        
        if prompt_used == "fs":
            prompt = f"{few_shot_prompt}\n{q}"
        if prompt_used == "fs_inst":
            if answer_mode == 'da':
                prompt = f"{few_shot_prompt}\n{q}\nDo not generate your explaination, please give the answer only as follow:\n\
                    Answer:."
            if answer_mode == 'cot':
                prompt = f"{few_shot_prompt}\n{q}\nPlease generate your explanation first, then generate the answer in the bracket as follow:\n" +"Answer: {}"
            if answer_mode == 'grounding_cot':
                # prompt = f"{few_shot_prompt}\n{q}\nI want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags and then generate your answers. The output format is as follow:\n\
                #     Reformatted Question: \
                #         Answer:"
            
                prompt = f"{few_shot_prompt}\n{q}\nI want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags for key phrases, the key phrases that are most relevant to answering the question {last_sentence} and then generate your answers. The output format is as follow:\n\
                    Reformatted Question: \
                        Answer:"
        if prompt_used == "zs":
            prompt = f"{q}\nI want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags (<fact1>, <fact2>, <fact3>, etc) for key phrases, the key phrases that are most relevant to answering the question {last_sentence}, and then generate your answers that also have the tag (<fact1>, <fact2>, <fact3>, etc) for the grounded information. Give your answer by analyzing step by step, and give only numbers in the final answer. The output format is as follow:\n\
                Reformatted Question: \
                    Answer:\
                        Final answer:"   
            # prompt = f"{q}\nGive your answer by analyzing step by step, and give only numbers in the final answer. The output format is as follow:\n\
            #         Answer:\
            #             Final answer:"   
        if llm_model == 'gemini':
            genai.configure(api_key=API_KEYS['gemini'])
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            try:
                response = model.generate_content(prompt, request_options=RequestOptions(retry=retry.Retry(initial=10, multiplier=2, maximum=60, timeout=60)))
                answers.append(response.text)
                questions_can_be_answered.append(q)
                ids_can_be_answered.append(id)
            except:
                continue
            
        elif llm_model == 'claude':
            client = anthropic.Anthropic(api_key=API_KEYS['claude'])
            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )
                answers.append(response.content[0].text)
                questions_can_be_answered.append(q)
                ids_can_be_answered.append(id)
            except:
                continue
    
    return ids_can_be_answered, questions_can_be_answered, answers

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--llm_model', type=str, default='gemini', help='The language model to query', choices=['gemini', 'claude'])
    arg_parser.add_argument('--dataset', type=str, default='GSM8K', help='The dataset to query', choices=['GSM8K', 'StrategyQA', 'p_GSM8K', 'AQUA', 'MultiArith', 'ASDiv', 'SVAMP'])
    arg_parser.add_argument('--prompt_used', type=str, default='fs_inst', help='The prompt used to query the language model', choices=['zs', 'fs', 'fs_inst'])
    arg_parser.add_argument('--answer_mode', type=str, default='da', help='The answer mode', choices=['da', 'cot', 'grounding_cot'])
    arg_parser.add_argument('--save_answer', action='store_true')
    
    args = arg_parser.parse_args()
    
    prompt_design = 'design_1'
    version = 'v4'
    
    # data path
    if args.dataset == 'p_GSM8K':
        data_path = f'data/p_GSM8K/r-gsm.jsonl'
        fewshot_prompt_path = f"prompt/GSM8K/fewshot_{prompt_design}_{version}.txt"
    else:
        data_path = f'data/{args.dataset}/test.jsonl'
    
    # fewshot_prompt_path = f"prompt/{args.dataset}/fewshot_{prompt_design}_{version}.txt"
    # fewshot_prompt_path = f"prompt/{args.dataset}/fewshot_da.txt"
    if args.answer_mode in ['da', 'cot']:
        fewshot_prompt_path = f"prompt/GSM8K/fewshot_{args.answer_mode}.txt"
    if args.answer_mode == 'grounding_cot':
        fewshot_prompt_path = f"prompt/GSM8K/fewshot_{prompt_design}_{version}.txt"
    
    
    # save path
    if args.answer_mode == 'grounding_cot':
        save_path = f'results/{args.dataset}/{prompt_design}_{version}/{args.prompt_used}_{args.llm_model}.csv'
        os.makedirs(f'results/{args.dataset}/{prompt_design}_{version}', exist_ok=True)
    if args.answer_mode in ['da', 'cot']:
        save_path = f'results/{args.dataset}/{args.answer_mode}/{args.prompt_used}_{args.llm_model}.csv'
        os.makedirs(f'results/{args.dataset}/{args.answer_mode}', exist_ok=True)
    
    # read file grounding_prompt.txt
    with open(fewshot_prompt_path, 'r') as file:
        few_shot_prompt = file.read()
        
    # read data
    data = read_jsonl_file(data_path)
    random_data = data
    
    question_length = 252 # 336  # 526 # 800
    # questions = [x["question"] for x in random_data if len(x["question"]) >= question_length]
    # ids = [x["id"] for x in random_data if len(x["question"]) >= question_length]
    
    questions = [x["question"] for x in random_data if len(x["question"]) >= question_length]
    ids = [x["id"] for x in random_data if len(x["question"]) >= question_length]
    
    # ------------------------------
    # read infered id
    # infered_data = pd.read_csv(f'results/GSM8K/design_1_v4/fs_inst_{args.llm_model}_20_longest.csv')
    # infered_ids = infered_data['id'].tolist()
    # remove questions and ids that have been infered, so we can infer the rest of the questions
    # remaining_questions, remaining_ids = [], []
    # for q, id in zip(questions, ids):
    #     if id not in infered_ids:
    #         remaining_questions.append(q)
    #         remaining_ids.append(id)
    # questions = remaining_questions
    # ids = remaining_ids
    # questions = questions[:1]
    # ids = ids[:1]
    # ------------------------------
    ids_can_be_answered, questions_can_be_answered, answers = query_llm(args.llm_model, ids, questions, few_shot_prompt, args.prompt_used, args.answer_mode)
    
    if args.save_answer:
        # save answers and questions to csv file (the len of question and answer should be the same)
        df = pd.DataFrame({'id': ids_can_be_answered, 'question': questions_can_be_answered, 'answer': answers})
        df.to_csv(save_path, index=False)