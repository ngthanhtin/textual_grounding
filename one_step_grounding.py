
import yaml, os, re, random, json
from tqdm import tqdm
import pandas as pd

from arg_parser import get_common_args
from utils.utils import read_jsonl_file, extract_last_sentence
from agents.api_agents import api_agent
from agents.batch_api_agents import batch_api_agent

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
            
    # load config file
    # data_path & fewshot_prompt_path & max_question_length
    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    base_data_path = args.base_data_path
    data_path = os.path.join(base_data_path, config['data_paths'][args.dataset])
    base_prompt_path = args.base_prompt_path
    base_prompt_path = 'prompt_auto_tagging/'
    fewshot_prompt_path = os.path.join(base_prompt_path, config['prompts'][args.answer_mode][args.dataset])
    question_length = config['max_question_lengths'][args.dataset]
            
    # read data
    if 'jsonl' in data_path:
        data = read_jsonl_file(data_path)
    else:
        with open(data_path, 'r') as file:
            data = json.load(file)
    
    # read file grounding_prompt.txt
    with open(fewshot_prompt_path, 'r') as file:
        few_shot_prompt = file.read()
        
    if args.data_mode == 'random':
        question_length = 0
    
    question_length = 0
    random_data = data        
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
    elif args.dataset == 'spartQA':
        questions = [x['question'].replace('0:', '(a)').replace('1:', '(b)').replace('2:', '(c)').replace('3:', '(d)') for x in random_data if len(x["question"]) >= question_length]
        ids = [x["id"] for x in random_data if len(x["question"]) >= question_length]
    elif args.dataset == 'reclor':
        questions = [x['context'] + ' ' + x["question"] + '\n(a) ' + x['answers'][0] + '\n(b) ' + x['answers'][1] + '\n(c) ' + x['answers'][2] + '\n(d) ' + x['answers'][3] for x in random_data if len(x["question"]) >= question_length]
        ids = [x["id_string"] for x in random_data if len(x["question"]) >= question_length]
    elif args.dataset == 'GSM_IC':
        questions = [x['new_question'] for x in random_data if len(x["new_question"]) >= question_length]
        ids = [i for i in range(len(questions))]
    elif args.dataset == 'GSM8K_Hard':
        questions = [x['question'] for x in random_data if len(x["question"]) >= question_length]
        ids = [i for i in range(len(questions))]
    else:
        questions = [x["question"] for x in random_data if len(x["question"]) >= question_length]
        if args.dataset == 'GSM_Plus':
            ids = [i for i in range(len(questions))]
        elif args.dataset in ['coin', 'last_letter_2', 'last_letter_4']:
            ids = [i for i in range(len(questions))]
        elif args.dataset == 'wikimultihopQA':
            ids = [x["_id"] for x in random_data if len(x["question"]) >= question_length]
        else:
            ids = [x["id"] for x in random_data if len(x["question"]) >= question_length]
    
    # ------------------------------
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
    
    # ------------------------------
    # batch request only supports gpt-4o for now
    args.batch_request = False
    if not args.batch_request:
        ids_can_be_answered, questions_can_be_answered, answers = query_llm(args.llm_model, ids, questions, args.dataset, few_shot_prompt, args.prompt_used, args.temperature, args.answer_mode)
    else:
        batch_query_llm(args.llm_model, ids, questions, args.dataset, few_shot_prompt, args.prompt_used, args.temperature, args.answer_mode)
    
    if args.save_answer:
        if args.batch_request:
            print('Batch request is used, please check the result in the batch_request folder')
        else: 
            # save answers and questions to csv file (the len of question and answer should be the same)
            df = pd.DataFrame({'id': ids_can_be_answered, 'question': questions_can_be_answered, 'answer': answers})
            df.to_csv(save_path, index=False)