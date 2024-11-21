
import yaml, os, re, random, json
from tqdm import tqdm
import pandas as pd

from arg_parser import get_common_args
from utils.utils import read_jsonl_file, extract_last_sentence
from agents.api_agents import api_agent
from agents.batch_api_agents import batch_api_agent
from load_dataset import DatasetLoader

random.seed(0)

def create_prompt(question, dataset, prompt_used, few_shot_prompt, answer_mode):
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
    else:
        last_sentence = extract_last_sentence(question)
    
    if prompt_used == "fs":
        prompt = f"{few_shot_prompt}\n{question}"
        
    if prompt_used == "fs_inst":
        if answer_mode == 'da':
            prompt = f"{few_shot_prompt}\n{question}\nDo not generate your explaination, please give the answer only as follow:\n\
                Answer:."
        if answer_mode == 'cot':
            prompt = f"{few_shot_prompt}\n{question}\nPlease generate your explanation first, then generate the final answer in the bracket as follow:\n" +"Answer: {}"
        if answer_mode == 'grounding_cot':
            #(ground in Q and A)
            instruction = f"I want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags for key phrases, the key phrases that are most relevant to answering the question {last_sentence} and then generate your answers. The output format is as follow:\n\
                Reformatted Question: \
                    Answer:"
                    
            #(ground in Q only)
            # instruction = "I want you to answer this question. To do that, first, re-generate the question with proper tags for key phrases, the key phrases that are most relevant to answering the question {last_sentence}, and then generate your answers. The output format is as follow:\n\
            #     Reformatted Question: \
            #         Answer:"
                    
            # (ground in A only)
            # instruction = f"I want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, repeat the question and then, generate your answers with proper tags for key phrases, the key phrases that are most relevant to answering the question {last_sentence}. The output format is as follow:\n\
            #     Reformatted Question: \
            #         Answer:"
            
            prompt = f"{few_shot_prompt}\n{question}\n{instruction}"
            
    if prompt_used == "zs":
        instruction = "I want you to answer this question but your explanation should contain references referring back to the information in the question. To do that, first, re-generate the question with proper tags (<fact1>, <fact2>, <fact3>, etc) for key phrases, the key phrases that are most relevant to answering the question {last_sentence}, and then generate your answers that also have the tag (<fact1>, <fact2>, <fact3>, etc) for the grounded information. Give your answer by analyzing step by step, and give your answer in curly brackets" + " {} in the final answer. The output format is as follow:\n\
            Reformatted Question: \
                Answer:\
                    Final answer:"
                    
        prompt = f"{question}\n{instruction}"
    
    return prompt
    
def batch_query_llm(llm_model, ids, questions, dataset, few_shot_prompt, prompt_used, temperature=1.0, answer_mode='da'):
    prompts = []

    for i, (id, q) in tqdm(enumerate(zip(ids, questions))):
        prompt = create_prompt(q, dataset, prompt_used, few_shot_prompt, answer_mode)
        prompts.append(prompt)
        
    batch_output_file = f'batch_request/{dataset}/{answer_mode}/records.jsonl'
    os.makedirs(f'batch_request/{dataset}', exist_ok=True)
    result_file = f'batch_request/{args.dataset}/{answer_mode}/{prompt_used}_{llm_model}.jsonl'
    os.makedirs(f'batch_request/{args.dataset}/{answer_mode}', exist_ok=True)
    
    
    batch_api_agent(llm_model, ids, prompts, temperature=temperature, batch_output_file=batch_output_file, result_file=result_file)
    

def query_llm(llm_model, ids, questions, dataset, few_shot_prompt, prompt_used, temperature=1.0, answer_mode='da'):
    answers = []
    ids_can_be_answered = []
    questions_can_be_answered = []
    
    for i, (id, q) in tqdm(enumerate(zip(ids, questions))):
        
        prompt = create_prompt(q, dataset, prompt_used, few_shot_prompt, answer_mode)
        
        # if i == 1:
        #     print('haha')
        #     break
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
    
    return ids_can_be_answered, questions_can_be_answered, answers

if __name__ == "__main__":
    
    arg_parser = get_common_args()  # Get the common arguments
    args = arg_parser.parse_args()
    
    prompt_design = 'design_1'
    version = 'v4'
    
    # save path
    save_result_folder = args.base_result_path
    save_result_folder = 'results_auto_tagging'
    if args.answer_mode in ['da', 'cot']:
        save_path = f'{save_result_folder}/{args.dataset}/{args.answer_mode}/{args.prompt_used}_{args.llm_model}.csv'
        os.makedirs(f'{save_result_folder}/{args.dataset}/{args.answer_mode}', exist_ok=True)
    if args.answer_mode == 'grounding_cot':
        save_path = f'{save_result_folder}/{args.dataset}/{prompt_design}_{version}/{args.prompt_used}_{args.llm_model}.csv'
        os.makedirs(f'{save_result_folder}/{args.dataset}/{prompt_design}_{version}', exist_ok=True)
    
    str_temperature = str(args.temperature).replace('.', '')
    if args.data_mode == 'random':
        save_path = save_path[:-4] + f'_temp_{str_temperature}_random.csv'
    else:
        save_path = save_path[:-4] + f'_temp_{str_temperature}_longest.csv'
            
    # data loader --> load fs prompt, data questions and ids
    args.base_data_path = args.base_data_path
    args.base_prompt_path = 'prompt_auto_tagging/'
        
    dataloader = DatasetLoader(config_path='configs/config.yaml', base_data_path=args.base_data_path, base_few_shot_prompt_path=args.base_prompt_path, dataset=args.dataset, data_mode=args.data_mode, num_samples=args.num_samples)
                    
    questions, ids = dataloader.get_questions_and_ids()
    few_shot_prompt = dataloader._load_few_shot_prompt(fs_mode=args.answer_mode)
    
    # -------run remaining questions
    remain = False
    if remain:
        # read infered id
        if args.answer_mode == 'grounding_cot':
            infered_path = f'/Users/tinnguyen/Downloads/LAB_PROJECTS/textual_grounding/results_auto_tagging/{args.dataset}/design_1_v4/fs_inst_llama_sambanova_70b_temp_10_longest.csv'
        elif args.answer_mode == 'cot':
            infered_path = f'/Users/tinnguyen/Downloads/LAB_PROJECTS/textual_grounding/results_auto_tagging/{args.dataset}/cot/fs_inst_llama_sambanova_70b_temp_10_longest.csv'
            
        save_path = save_path[:-4] + '_remain.csv'
        infered_data = pd.read_csv(infered_path)
        infered_ids = infered_data['id'].tolist()
        # remove questions and ids that have been infered, so we can infer the rest of the questions
        remaining_questions, remaining_ids = [], []
        for q, id in zip(questions, ids):
            if id not in infered_ids:
                remaining_questions.append(q)
                remaining_ids.append(id)
        
        questions = list(remaining_questions)
        ids = list(remaining_ids)
    
    # batch request only supports gpt-4o for now
    if not args.batch_request:
        ids_can_be_answered, questions_can_be_answered, answers = query_llm(args.llm_model, ids, questions, args.dataset, few_shot_prompt, args.prompt_used, args.temperature, args.answer_mode)
    else: # now only support gpt4
        if 'gpt' in args.llm_model:
            batch_query_llm(args.llm_model, ids, questions, args.dataset, few_shot_prompt, args.prompt_used, args.temperature, args.answer_mode)
        else:
            raise ValueError('Batch request only supports gpt-4o now')
    
    
    # save answers
    if args.save_answer:
        if args.batch_request:
            print('Batch request is used, please check the result in the batch_request folder')
        else: 
            # save answers and questions to csv file (the len of question and answer should be the same)
            df = pd.DataFrame({'id': ids_can_be_answered, 'question': questions_can_be_answered, 'answer': answers})
            df.to_csv(save_path, index=False)