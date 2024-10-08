import os, re
import random, json, argparse
from tqdm import tqdm
import pandas as pd

from utils.keys import API_KEYS
from utils.utils import read_jsonl_file, extract_last_sentence

# gemini
import google.generativeai as genai
from google.generativeai.types import RequestOptions
from google.api_core import retry
# claude
import anthropic
# llama
# from transformers import (AutoModelForCausalLM, 
#                           AutoTokenizer, 
#                           BitsAndBytesConfig, 
#                           pipeline)
# import torch
# import torch.nn as nn
# gpt4
from openai import OpenAI
import openai
# groq
import groq

random.seed(0)


def query_llm(llm_model, ids, questions, few_shot_prompt, prompt_used, answer_mode='da'):
    answers = []
    ids_can_be_answered = []
    questions_can_be_answered = []
    
    if llm_model == 'llama_transformer':
        model_id = "/home/tin/projects/Llama-2-7b-chat-hf"
        compute_dtype = getattr(torch, "float16")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True, 
            bnb_4bit_quant_type="nf4", 
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map='cuda:7',
            torch_dtype=compute_dtype,
            quantization_config=bnb_config, 
        )

        model.config.use_cache = False
        model.config.pretraining_tp = 1

        tokenizer = AutoTokenizer.from_pretrained(model_id, 
                                                trust_remote_code=True,
                                                )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        
    for i, (id, q) in tqdm(enumerate(zip(ids, questions))):
        
        if args.dataset == 'commonsenseQA':
            last_sentence_pattern = re.compile(r"Question:\s*(.*?)\s*([^.?!]*[.?!])\s*Answer Choices:", re.DOTALL)
            match = last_sentence_pattern.search(q)
            if match:
                last_sentence = match.group(2)
            else:
                last_sentence = 'the question'
        elif args.dataset == 'sports':
            last_sentence = 'Is the following sentence plausible?'
        else:
            last_sentence = extract_last_sentence(q)
        
        if i == 1:
            print(last_sentence)
            break
        
        if prompt_used == "fs":
            prompt = f"{few_shot_prompt}\n{q}"
        if prompt_used == "fs_inst":
            if answer_mode == 'da':
                prompt = f"{few_shot_prompt}\n{q}\nDo not generate your explaination, please give the answer only as follow:\n\
                    Answer:."
            if answer_mode == 'cot':
                prompt = f"{few_shot_prompt}\n{q}\nPlease generate your explanation first, then generate the final answer in the bracket as follow:\n" +"Answer: {}"
            if answer_mode == 'grounding_cot':
                # version 1
                # prompt = f"{few_shot_prompt}\n{q}\nI want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags and then generate your answers. The output format is as follow:\n\
                #     Reformatted Question: \
                #         Answer:"
            
                # version 2 (ground in Q and A)
                
                prompt = f"{few_shot_prompt}\n{q}\nI want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags for key phrases, the key phrases that are most relevant to answering the question {last_sentence} and then generate your answers. The output format is as follow:\n\
                    Reformatted Question: \
                        Answer:"
                
                # version 3 (ground in Q only)
                # prompt = f"{few_shot_prompt}\n{q}\nI want you to answer this question. To do that, first, re-generate the question with proper tags for key phrases, the key phrases that are most relevant to answering the question {last_sentence}, and then generate your answers. The output format is as follow:\n\
                #     Reformatted Question: \
                #         Answer:"
                        
                # version 4 (ground in A only)
                # prompt = f"{few_shot_prompt}\n{q}\nI want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, repeat the question and then, generate your answers with proper tags for key phrases, the key phrases that are most relevant to answering the question {last_sentence}. The output format is as follow:\n\
                #     Reformatted Question: \
                #         Answer:"
                
                # prompt = f"{few_shot_prompt}\n{q}\nI want you to answer this question. To do that, first, repeat the question, then generate your answers. The output format is as follow:\n\
                #     Repeated Question: \
                #         Answer:"
        if prompt_used == "zs":
            prompt = f"{q}\nI want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags (<fact1>, <fact2>, <fact3>, etc) for key phrases, the key phrases that are most relevant to answering the question {last_sentence}, and then generate your answers that also have the tag (<fact1>, <fact2>, <fact3>, etc) for the grounded information. Give your answer by analyzing step by step, and give your answer in curly brackets" + " {} in the final answer. The output format is as follow:\n\
                Reformatted Question: \
                    Answer:\
                        Final answer:"   
            # prompt = f"{q}\nGive your answer by analyzing step by step, and give only numbers in the final answer. The output format is as follow:\n\
            #         Answer:\
            #             Final answer:"   
        if 'gemini' in llm_model:
            genai.configure(api_key=API_KEYS['gemini'])
            model_config = {
                "temperature": 0,
                }
            model = genai.GenerativeModel(llm_model, 
                                          generation_config=model_config
                                          )
            try:
                response = model.generate_content(prompt, request_options=RequestOptions(retry=retry.Retry(initial=10, multiplier=2, maximum=60, timeout=60)))
                answers.append(response.text)
                questions_can_be_answered.append(q)
                ids_can_be_answered.append(id)
            except:
                continue
            
        elif 'claude' in llm_model:
            client = anthropic.Anthropic(api_key=API_KEYS['claude'])
            try:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=1024,
                    temperature = 0.0,
                    messages=[{"role": "user", "content": prompt}]
                )
                answers.append(response.content[0].text)
                questions_can_be_answered.append(q)
                ids_can_be_answered.append(id)
            except:
                continue
        elif 'gpt4' in llm_model:
            client = OpenAI(
                    api_key=API_KEYS['gpt4'],
                )
            try:
                response = client.chat.completions.create(
                            model=llm_model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.0,
                            n=1,
                            frequency_penalty=0,
                            presence_penalty=0
                        )
                choices = response.choices
                
                completion_objs = [choice.message for choice in choices]
                completions = [
                    completion.content for completion in completion_objs]

                answers.append(completions[0])
                questions_can_be_answered.append(q)
                ids_can_be_answered.append(id)
            except:
                continue
        elif llm_model == 'llama_transformer':    
            try:
                pipe = pipeline(task="text-generation", 
                            model='/home/tin/projects/Llama-2-7b-chat-hf', 
                            tokenizer=tokenizer, 
                            max_new_tokens = 1024, 
                            # temperature = 0.0, # llama default temp: 0.75
                            do_sample=False,
                        )
                result = pipe(prompt)
                answers.append(result[0]['generated_text'])
                questions_can_be_answered.append(q)
                ids_can_be_answered.append(id)
            except:
                continue
        elif llm_model == 'llama_groq':
            client = groq.Groq(api_key=API_KEYS['groq'])
            messages = [
                    {"role": "system", "content": """I am a language model that can help you with your questions. I can provide you with information, answer questions, and help you with your problems. I am here to help you.
            """ },
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "Let's think step by step."}
                ]
            try:
                response = client.chat.completions.create(
                                model="llama-3.1-70b-versatile",
                                messages=messages,
                                max_tokens=1024,
                                temperature=0.0,
                            )
                response = response.choices[0].message.content
                answers.append(response)
                questions_can_be_answered.append(q)
                ids_can_be_answered.append(id)
            except:
                continue
    
    return ids_can_be_answered, questions_can_be_answered, answers

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--llm_model', type=str, default='gemini', help='The language model to query', choices=['gemini-1.5-pro-002', 'gemini-1.5-flash-002', 'claude', 'gpt-4o-2024-08-06', 'gpt-4o-mini-2024-07-18', 'llama_transformer', 'llama_groq'])
    arg_parser.add_argument('--dataset', type=str, default='GSM8K', help='The dataset to query', choices=['GSM8K', 'StrategyQA', 'p_GSM8K', 'AQUA', 'MultiArith', 'ASDiv', 'SVAMP', 'commonsenseQA', 'date', 'sports', 'reclor', 'CLUTRR'])
    arg_parser.add_argument('--prompt_used', type=str, default='fs_inst', help='The prompt used to query the language model', choices=['zs', 'fs', 'fs_inst'])
    arg_parser.add_argument('--answer_mode', type=str, default='da', help='The answer mode', choices=['da', 'cot', 'grounding_cot'])
    arg_parser.add_argument('--save_answer', action='store_true')
    arg_parser.add_argument('--data_mode', type=str, default='longest', help='The data mode', choices=['random', 'longest'])
    
    args = arg_parser.parse_args()
    
    prompt_design = 'design_1'
    version = 'v4'
    
    # data path
    if args.dataset == 'p_GSM8K':
        data_path = f'data/p_GSM8K/r-gsm.jsonl'
    else:
        data_path = f'data/{args.dataset}/test.jsonl'
    
    # fewshot_prompt_path = f"prompt/{args.dataset}/fewshot_{prompt_design}_{version}.txt"
    # fewshot_prompt_path = f"prompt/{args.dataset}/fewshot_da.txt"
    if args.answer_mode in ['da', 'cot']:
        if args.dataset in ['GSM8K', 'MultiArith', 'ASDiv', 'p_GSM8K']:
            fewshot_prompt_path = f"prompt/GSM8K/fewshot_{args.answer_mode}.txt"
        elif args.dataset in ['StrategyQA', 'SVAMP', 'AQUA', 'commonsenseQA', 'date', 'sports', 'reclor', 'CLUTRR']:
            fewshot_prompt_path = f"prompt/{args.dataset}/fewshot_{args.answer_mode}.txt"
            
    if args.answer_mode == 'grounding_cot':
        if args.dataset in ['GSM8K', 'MultiArith', 'ASDiv', 'p_GSM8K']:
            fewshot_prompt_path = f"prompt/GSM8K/fewshot_{prompt_design}_{version}.txt"
        elif args.dataset in ['StrategyQA', 'SVAMP', 'AQUA', 'commonsenseQA', 'date', 'sports', 'reclor', 'CLUTRR']:
            fewshot_prompt_path = f"prompt/{args.dataset}/fewshot_{prompt_design}_{version}.txt"
    
    # save path
    if args.answer_mode == 'grounding_cot':
        save_path = f'results/{args.dataset}/{prompt_design}_{version}/{args.prompt_used}_{args.llm_model}.csv'
        os.makedirs(f'results/{args.dataset}/{prompt_design}_{version}', exist_ok=True)
    if args.answer_mode in ['da', 'cot']:
        save_path = f'results/{args.dataset}/{args.answer_mode}/{args.prompt_used}_{args.llm_model}.csv'
        os.makedirs(f'results/{args.dataset}/{args.answer_mode}', exist_ok=True)
    
    #
    if args.data_mode == 'random':
        save_path = save_path[:-4] + '_temp_0_random.csv'
    else:
        save_path = save_path[:-4] + '_temp_0.csv'
    
    # read file grounding_prompt.txt
    with open(fewshot_prompt_path, 'r') as file:
        few_shot_prompt = file.read()
        
    # read data
    data = read_jsonl_file(data_path)
    random_data = data
    
    if args.dataset == 'p_GSM8K':
        question_length = 0
    elif args.dataset == 'MultiArith':
        question_length = 168
    elif args.dataset == 'ASDiv':
        question_length = 252
    elif args.dataset == 'GSM8K':
        question_length = 336
    elif args.dataset == 'AQUA':
        question_length = 200
    elif args.dataset == 'StrategyQA':
        question_length = 78
    elif args.dataset == 'SVAMP':
        question_length = 199
    elif args.dataset == 'commonsenseQA':
        question_length = 93
    elif args.dataset == 'sports':
        question_length = 48
    elif args.dataset == 'date':
        question_length = 105
    
    if args.data_mode == 'random':
        question_length = 0
    
    if args.dataset == 'p_GSM8K':
        questions = [x["new_question"] for x in random_data if len(x["new_question"]) >= question_length]
        ids = [x["index"] for x in random_data if len(x["new_question"]) >= question_length]
    elif args.dataset == 'commonsenseQA':
        questions, ids = [], []
        for sample in random_data:
            if len(sample['question']['stem']) >= question_length:
                question = sample['question']['stem']
                choices = sample['question']['choices']
                answer_choices = ''
                for choice in choices:
                    answer_choices += "(" + choice['label'].lower() + ") " + choice['text'] + "\n"
                questions.append(question + "\n" + answer_choices)
                ids.append(sample['id'])
    else:
        questions = [x["question"] for x in random_data if len(x["question"]) >= question_length]
        ids = [x["id"] for x in random_data if len(x["question"]) >= question_length]
    
    # ------------------------------
    if args.data_mode == 'random' and args.dataset != 'p_GSM8K':
        # read infered id
        if args.dataset in ['commonsenseQA', 'date', 'sports', 'reclor', 'CLUTRR']:
            infered_data = pd.read_csv(f'results/{args.dataset}/cot/fs_inst_gemini-1.5-pro-002_temp_0.csv')
        else:
            infered_data = pd.read_csv(f'results/{args.dataset}/cot/fs_inst_gemini_temp_0.csv')
        infered_ids = infered_data['id'].tolist()
        # remove questions and ids that have been infered, so we can infer the rest of the questions
        remaining_questions, remaining_ids = [], []
        for q, id in zip(questions, ids):
            if id not in infered_ids:
                remaining_questions.append(q)
                remaining_ids.append(id)
        # get random 200 questions, ids
        question_id_pairs = list(zip(remaining_questions, remaining_ids))
        random_pairs = random.sample(question_id_pairs, min(200, len(question_id_pairs))) 
        selected_questions, selected_ids = zip(*random_pairs)  # Unzips into two separate lists
        questions = list(selected_questions)
        ids = list(selected_ids)
        
        # questions = remaining_questions
        # ids = remaining_ids
    
    # ------------------------------
    ids_can_be_answered, questions_can_be_answered, answers = query_llm(args.llm_model, ids, questions, few_shot_prompt, args.prompt_used, args.answer_mode)
    
    if args.save_answer:
        # save answers and questions to csv file (the len of question and answer should be the same)
        df = pd.DataFrame({'id': ids_can_be_answered, 'question': questions_can_be_answered, 'answer': answers})
        df.to_csv(save_path, index=False)