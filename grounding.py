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


def query_llm(llm_model, ids, questions, few_shot_prompt, prompt_used):
    answers = []
    ids_can_be_answered = []
    questions_can_be_answered = []
    
    for id, q in tqdm(zip(ids, questions)):
        # prompt = f"{few_shot_prompt}\n{q}" # prompt 0
        # prompt = f"{few_shot_prompt}\n{q}\nCan you help me answer the question and use <a></a> tags to highlight important information and its reference to the information in the question by using <ref></ref> tags." # prompt 1
        # prompt = f"{q}\nCan you help me answer the question and use <a></a> tags to highlight important information and its reference to the information in the question by using <ref></ref> tags." # prompt zeroshot
        
        if prompt_used == "fs":
            prompt = f"{few_shot_prompt}\n{q}"
        if prompt_used == "fs_inst":
            prompt = f"{few_shot_prompt}\n{q}\nI want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags and then generate your answers. The output format is as follow:\n\
                Reformatted Question: \
                    Answer:"
        if prompt_used == "zs":
            prompt = f"{q}\nI want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags (<a>, <b>, <c>, etc) for refered information and then generate your answers that also have the tag (<a>, <b>, <c>, etc) for the grounded information. Give your answer by analyzing step by step, and give only numbers in the final answer. The output format is as follow:\n\
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
    arg_parser.add_argument('--dataset', type=str, default='GSM8K', help='The dataset to query', choices=['GSM8K', 'StrategyQA'])
    arg_parser.add_argument('--prompt_used', type=str, default='fs_inst', help='The prompt used to query the language model', choices=['zs', 'fs', 'fs_inst'])
    arg_parser.add_argument('--save_answer', action='store_true')
    
    args = arg_parser.parse_args()
    
    data_path = f'data/{args.dataset}/test.jsonl'
    fewshot_prompt_path = f"prompt/{args.dataset}/fewshot_grounding_prompt_design_1_fix.txt"
    save_path = f'results/{args.dataset}/design_1_fix/test_grounding_answer_prompt_{args.prompt_used}_{args.llm_model}.csv'
        
    # read file grounding_prompt.txt
    with open(fewshot_prompt_path, 'r') as file:
        few_shot_prompt = file.read()
        
    # read data
    data = read_jsonl_file(data_path)
    # take random data
    random_data = random.sample(data, 10)
    
    questions = [x["question"] for x in random_data]
    ids = [x["id"] for x in random_data]       
            
    ids_can_be_answered, questions_can_be_answered, answers = query_llm(args.llm_model, ids, questions, few_shot_prompt, args.prompt_used)
    
    if args.save_answer:
        # save answers and questions to csv file (the len of question and answer should be the same)
        df = pd.DataFrame({'id': ids_can_be_answered, 'question': questions_can_be_answered, 'answer': answers})
        df.to_csv(save_path, index=False)