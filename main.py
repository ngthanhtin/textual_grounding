
import os, re, random
from tqdm import tqdm
import pandas as pd

from arg_parser import get_common_args
from agents.api_agents import api_agent
from agents.batch_api_agents import batch_api_agent
from load_dataset import DatasetLoader

import re

# gemini
import google.generativeai as genai
from google.generativeai.types import RequestOptions
from google.api_core import retry

def remove_fact_tags_from_answers(prompt):
    # Use regex to remove <facti> tags from all answers in the string
    cleaned_prompt = re.sub(r"Answer:.*?(<fact\d+>.*?</fact\d+>.*?)(?=\n|$)", 
                            lambda match: "Answer: " + re.sub(r"</?fact\d+>", "", match.group(1)), 
                            prompt, 
                            flags=re.DOTALL)
    return cleaned_prompt

def remove_fact_tags_from_questions(prompt):
    # Use regex to remove <facti> tags from all answers in the string
    cleaned_prompt = re.sub(r"Reformatted Question:.*?(<fact\d+>.*?</fact\d+>.*?)(?=\n|$)", 
                            lambda match: "Reformatted Question: " + re.sub(r"</?fact\d+>", "", match.group(1)), 
                            prompt, 
                            flags=re.DOTALL)

    return cleaned_prompt

def extract_last_sentence(text):
    # Split the text into sentences using regular expression to handle punctuation.
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    
    # Return the last sentence after stripping any extra spaces.
    return sentences[-1].strip() if sentences else text

def med_QA_extract_last_sentence(text):
    # Split the text at the point where multiple-choice options start (e.g., "A)", "B)", etc.)
    parts = re.split(r'\n[A-Z]\)', text, flags=re.MULTILINE)
    
    if parts:
        # The first part contains everything before the options
        pre_options = parts[0]
        
        # Use a regex to find all sentences ending with ., ?, or !
        sentences = re.findall(r'[^.!?]*[.!?]', pre_options, re.DOTALL)
        
        if sentences:
            # Return the last sentence after stripping any extra spaces
            return sentences[-1].strip()
    
    # If splitting or finding sentences fails, return the original text
    return text

def create_prompt(question, dataset, prompt_used, few_shot_prompt, answer_mode, tail):
    if dataset in ['commonsenseQA']:
        last_sentence_pattern = re.compile(r"Question:\s*(.*?)\s*([^.?!]*[.?!])\s*Answer Choices:", re.DOTALL)
        match = last_sentence_pattern.search(question)
        if match:
            last_sentence = match.group(2)
        else:
            last_sentence = 'the question'
    elif dataset == 'sports':
        last_sentence = 'Is the following sentence plausible?'
    elif dataset == 'reclor':
        last_sentence = 'Choose the correct answer.'
    elif dataset == 'spartQA':
        last_sentence = ""
    elif dataset == 'medQA':
        last_sentence = med_QA_extract_last_sentence(question)
    else:
        last_sentence = extract_last_sentence(question)
    
    if prompt_used == "fs":
        prompt = f"{few_shot_prompt}\n{question}"
        
    if prompt_used == "fs_inst":
        if answer_mode == 'da':
            prompt = f"{few_shot_prompt}\n{question}\nDo not generate your explaination, please give the answer only as follow:\n\
                Answer:."
        if answer_mode == 'cot':
            # randomness = random.randint(1, 9999)
            # prompt = f'[ID: {randomness}]' # add randomness   
            # print(randomness)
            prompt = f"{few_shot_prompt}\n{question}\nPlease generate your explanation first, then generate the final answer in the bracket as follow:\n" +"Answer: {}"
            # prompt = f"{question}"
            
            # print(prompt)
            
        if answer_mode == 'hot':
            #(ground in Q and A)
            if tail == '':
                instruction = f"I want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags for key phrases, the key phrases that are most relevant to answering the question {last_sentence} and then generate your answers. The output format is as follow:\n\
                    Reformatted Question: \
                        Answer: "
                
                # random_tag
                # instruction = f"I want you to answer this question. The output format is as follows:\n\
                #     Reformatted Question: \
                #         Answer:"
            # # change in A
            
            # instruction = f"I want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags for key phrases, ensuring that these tags are meaningful for answering the question. Then, in your explanation, include references using mismatched or irrelevant tags in the answer. The output format is as follows:
            #     Reformatted Question: \
            #         Answer:"
                    
            #(ground in Q only)
            if tail == '_only_ground_Q':
                instruction = f"I want you to answer this question. To do that, first, re-generate the question with proper tags for key phrases, the key phrases that are most relevant to answering the question {last_sentence}, and then generate your answers. The output format is as follow:\n\
                    Reformatted Question: \
                        Answer:"
                    
            # (ground in A only)
            if tail == '_only_ground_A':
                instruction = f"I want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, repeat the question and then, generate your answers with proper tags for key phrases, the key phrases that are most relevant to answering the question {last_sentence}. The output format is as follow:\n\
                Reformatted Question: \
                    Answer:"
            
            # repeat the question
            if tail == '_repeat_Q':
                instruction = f"I want you to answer this question. To do that, first, repeat the question and then, generate your answers. The output format is as follow:\n\
                Reformatted Question: \
                    Answer:"
                    
            prompt = f"{few_shot_prompt}\n{question}\n{instruction}"
            
    if prompt_used == "zs":
        instruction = "I want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags (<fact1>, <fact2>, <fact3>, etc) for key phrases, the key phrases that are most relevant to answering the question {last_sentence}, and then generate your answers that also have the tag (<fact1>, <fact2>, <fact3>, etc) for the grounded information. Give your answer by analyzing step by step, and give your answer in curly brackets" + " {} in the final answer. The output format is as follow:\n\
            Reformatted Question: \
                Answer:\
                    Final answer:"
                    
        prompt = f"{question}\n{instruction}"
    
    return prompt
    
def batch_query_llm(llm_model, ids, questions, dataset, few_shot_prompt, prompt_used, tail, temperature=1.0, answer_mode='da'):
    prompts = []

    for i, (id, q) in tqdm(enumerate(zip(ids, questions))):
        prompt = create_prompt(q, dataset, prompt_used, few_shot_prompt, answer_mode, tail)
        prompts.append(prompt)
        
    batch_output_file = f'batch_request/{dataset}/{answer_mode}/records.jsonl'
    os.makedirs(f'batch_request/{dataset}', exist_ok=True)
    result_file = f'batch_request/{args.dataset}/{answer_mode}/{prompt_used}_{llm_model}.jsonl'
    os.makedirs(f'batch_request/{args.dataset}/{answer_mode}', exist_ok=True)
    
    
    batch_api_agent(llm_model, ids, prompts, temperature=temperature, batch_output_file=batch_output_file, result_file=result_file)
    
def query_llm(llm_model, ids, questions, dataset, few_shot_prompt, prompt_used, tail, temperature=1.0, answer_mode='da', save_path='results.csv'):
    answers = []
    ids_can_be_answered = []
    questions_can_be_answered = []
    
    # init csv file
    with open(save_path, 'w') as f:
        f.write('id,question,answer\n')
    f.close()
    
    for i, (id, q) in tqdm(enumerate(zip(ids, questions))):
        
        prompt = create_prompt(q, dataset, prompt_used, few_shot_prompt, answer_mode, tail)
        
        # query three times if response is None
        response = None
        counter = 0
        while response is None:
            if counter == 3 or response is not None:
                break
            response = api_agent(llm_model, prompt, temperature=temperature)
        
        if response is not None:
            answers.append(response)
            questions_can_be_answered.append(q)
            ids_can_be_answered.append(id)
        else:
            print(f"Failed to generate answer for question {i}")
            continue

        # append id, question, answer to the csv file
        with open(save_path, 'a') as f:
            f.write(f"{id},{q},{response}\n")

        
    return ids_can_be_answered, questions_can_be_answered, answers

if __name__ == "__main__":
    
    arg_parser = get_common_args()  # Get the common arguments
    args = arg_parser.parse_args()
    
    # save path
    save_result_folder = args.base_result_path
    save_result_folder = 'results_auto_tagging'
    save_result_folder = 'results_auto_tagging_3'
    save_result_folder = 'results_auto_tagging_6'
    save_result_folder = 'results_auto_tagging_7'
    save_result_folder = 'results_deepseek'
    
    # save result path
    save_path = f'{save_result_folder}/{args.dataset}/{args.answer_mode}/{args.prompt_used}_{args.llm_model}.csv'
    os.makedirs(f'{save_result_folder}/{args.dataset}/{args.answer_mode}', exist_ok=True)
    
    str_temperature = str(args.temperature).replace('.', '')
    # tail = '_random_tag_Q'
    # tail = '_only_ground_A'
    # tail = '_only_ground_Q'
    # tail = '_repeat_Q'
    tail = ''
    # print(tail)
    save_path = save_path[:-4] + f'_temp_{str_temperature}_{args.data_mode}{tail}.csv'
    
            
    # data loader --> load fs prompt, data questions and ids
    args.base_data_path = args.base_data_path
    args.base_prompt_path = 'fewshot_prompts/'
        
    dataloader = DatasetLoader(config_path='configs/config.yaml', base_data_path=args.base_data_path, base_few_shot_prompt_path=args.base_prompt_path, dataset=args.dataset, data_mode=args.data_mode, num_samples=args.num_samples)
                    
    questions, ids = dataloader.get_questions_and_ids()
    print(f"Number of questions: {len(questions)}")
    
    few_shot_prompt = dataloader._load_few_shot_prompt(fs_mode=args.answer_mode)
    # remove tags
    # few_shot_prompt = remove_fact_tags_from_answers(few_shot_prompt)
    # few_shot_prompt = remove_fact_tags_from_questions(few_shot_prompt)
    # replace <fact1>, <fact2>, <fact3> with '<1>, <2>, <3>'
    if tail == '_repeat_Q':
        few_shot_prompt = remove_fact_tags_from_answers(few_shot_prompt)
        few_shot_prompt = remove_fact_tags_from_questions(few_shot_prompt)
    if tail == '_only_ground_Q':
        few_shot_prompt = remove_fact_tags_from_answers(few_shot_prompt)
    if tail == '_only_ground_A':
        few_shot_prompt = remove_fact_tags_from_questions(few_shot_prompt)
        few_shot_prompt = re.sub(r'Reformatted Question:.*?\n', '', few_shot_prompt)
    
    # -------run remaining questions
    if args.data_mode == 'remain':
        # read infered id
        infered_path = f'results_auto_tagging/{args.dataset}/{args.answer_mode}/fs_inst_llama_sambanova_70b_temp_10_longest.csv'
            
        infered_data = pd.read_csv(infered_path)
        infered_ids = infered_data['id'].tolist()
        
        questions, ids = dataloader.get_remaining_questions_and_ids(infered_ids)
    
    # batch request only supports gpt-4o for now
    if not args.batch_request:
        ids_can_be_answered, questions_can_be_answered, answers = query_llm(args.llm_model, ids, questions, args.dataset, few_shot_prompt, args.prompt_used, tail, args.temperature, args.answer_mode, save_path)
    else: # now only support gpt4
        if 'gpt' in args.llm_model:
            batch_query_llm(args.llm_model, ids, questions, args.dataset, few_shot_prompt, args.prompt_used, tail, args.temperature, args.answer_mode)
        else:
            raise ValueError('Batch request only supports gpt-4o now')
    
    
    # save answers
    # if args.save_answer:
    #     if args.batch_request:
    #         print('Batch request is used, please check the result in the batch_request folder')
    #     else: 
    #         # save answers and questions to csv file (the len of question and answer should be the same)
    #         df = pd.DataFrame({'id': ids_can_be_answered, 'question': questions_can_be_answered, 'answer': answers})
    #         df.to_csv(save_path, index=False)