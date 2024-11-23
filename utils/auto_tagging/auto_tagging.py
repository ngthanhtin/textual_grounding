import re, os

# gemini
import google.generativeai as genai
from google.generativeai.types import RequestOptions
from google.api_core import retry
#oopenAI
from openai import OpenAI

from keys import API_KEYS

from vis_auto_tagging.examples_for_grounding_in_question import examples_for_grounding_in_question, instruction_for_grounding_in_question
from vis_auto_tagging.examples_for_grounding_in_answer import  examples_for_grounding_in_answer, instruction_for_grounding_in_answer

# read fs prompt
def read_question_triples(filename):
    # Define data structure to hold triples
    triples = []

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.readlines()
        
        # Temporary storage for each triple
        current_triple = {"Question": "", "Answer": ""}
        current_section = None
        
        for line in content:
            line = line.strip()
            
            if line.startswith("Question:"):
                if current_triple["Question"]:  # Save the previous triple if it exists
                    triples.append(current_triple)
                    current_triple = {"Question": "", "Answer": ""}
                current_section = "Question"
                current_triple["Question"] = line[len("Question:"):].strip()
            elif line.startswith("Answer:"):
                current_section = "Answer"
                current_triple["Answer"] = line[len("Answer:"):].strip()
            elif line:  # Continue appending to the current section if not empty
                current_triple[current_section] += " " + line
        
        # Append the last triple if it's non-empty
        if current_triple["Question"]:
            triples.append(current_triple)
        
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    return triples
    
def detect_facts_in_question(fewshot_cot_file, instruction, examples):
    """
    Input: "{examples}\n{question}\n{instruction}"
    """
    triple_content = read_question_triples(fewshot_cot_file)
    
    responses = []
    for i, triple in enumerate(triple_content):
        # if i == 2:
        #     break

        question = triple["Question"]
        
        prompt = f"{examples}\n{question}\n\n{instruction}"
        try:
            genai.configure(api_key=API_KEYS['gemini'])
            model_config = {
                    "temperature": 0,
                    }
            model = genai.GenerativeModel('gemini-1.5-pro-002', 
                                            # generation_config=model_config
                                            )
            response = model.generate_content(prompt, request_options=RequestOptions(retry=retry.Retry(initial=10, multiplier=2, maximum=60, timeout=60)))
            response = response.text
            
            # client = OpenAI(
            #         api_key=API_KEYS['gpt4'],
            #     )
            # # try:
            # response = client.chat.completions.create(
            #             model='gpt-4o-2024-08-06',
            #             messages=[{"role": "user", "content": prompt}],
            #             temperature=1.0,
            #             n=1,
            #             frequency_penalty=0,
            #             presence_penalty=0
            #         )
            # choices = response.choices
            
            # completion_objs = [choice.message for choice in choices]
            # completions = [
            #     completion.content for completion in completion_objs]
            # response = completions[0]

            responses.append(response)
        except:
            print(f"Can not answer the question {i}")
            continue
    return responses

def grounding_facts_to_QA(fewshot_cot_file, detected_key_fact_file, instruction, examples):
    """
    Input: "{examples}\n{Key_facts}\n{question}\n{answer}\n{instruction}"
    """
    triple_content = read_question_triples(fewshot_cot_file)
    
    # with open(detected_key_fact_file, 'r') as file:
    #     file_content = file.read()

    # Using regex to extract each "Key Information" block
    # blocks = re.findall(r'Key Information:\n(.*?)(?=\n\n|$)', file_content, re.DOTALL)

    # Splitting each block by newlines and storing as list of lists
    # extracted_blocks = [block.strip().split('\n') for block in blocks]
    
    with open(detected_key_fact_file, 'r') as file:
        file_content = file.readlines()
    extracted_blocks = [line.strip() for line in file_content if line != '\n']
    
    responses = []
    for i, (triple, detected_key_fact) in enumerate(zip(triple_content, extracted_blocks)):
        # if i == 2:
        #     break

        question = triple["Question"]
        answer = triple["Answer"]
        
        prompt = f"{examples}\n### TAGGED QUESTION:\n{detected_key_fact}\n### ANSWER:\n{answer}\n{instruction}"
        # prompt = f"{examples}\nKey Information:\n{detected_key_fact}\n{question}\n{answer}\n{instruction}"
        
        try:
            genai.configure(api_key=API_KEYS['gemini'])
            model_config = {
                    "temperature": 0,
                    }
            model = genai.GenerativeModel('gemini-1.5-pro-002', 
                                            # generation_config=model_config
                                            )
            response = model.generate_content(prompt, request_options=RequestOptions(retry=retry.Retry(initial=10, multiplier=2, maximum=60, timeout=60)))
            response = response.text
            
            # client = OpenAI(
            #         api_key=API_KEYS['gpt4'],
            #     )
            # response = client.chat.completions.create(
            #             model='gpt-4o-2024-08-06',
            #             messages=[{"role": "user", "content": prompt}],
            #             temperature=1.0,
            #             n=1,
            #             frequency_penalty=0,
            #             presence_penalty=0
            #         )
            # choices = response.choices
            
            # completion_objs = [choice.message for choice in choices]
            # completions = [
            #     completion.content for completion in completion_objs]
            # response = completions[0]
            
            responses.append(response)
        except:
            print(f"Can not grounding {i}")
            continue
    
    return responses

if __name__ == '__main__':
    version = 'v13'
    # dataset = 'reasoning_about_colored_objects'
    # datasets = ['AQUA', 'ASDiv', 'GSM8K', 'SVAMP', 'MultiArith',  'StrategyQA', 'wikimultihopQA', 'causal_judgement', 'coin', 'date', 'reclor', 'navigate', 'commonsenseQA', 'logical_deduction_seven_objects', 'reasoning_about_colored_objects']
    datasets = ['AQUA', 'ASDiv', 'GSM8K', 'SVAMP', 'MultiArith']
    datasets = ['commonsenseQA']
    
    # mode = 'detect'
    mode = 'ground'
    
    for dataset in datasets:
        fewshot_cot_file_path = f'../prompt/{dataset}/fewshot_cot.txt'
        detected_key_fact_file = f'vis_auto_tagging/detect/{dataset}_detect_{version}.txt'
        if mode == 'detect':
            responses = detect_facts_in_question(fewshot_cot_file_path, instruction_for_grounding_in_question, examples_for_grounding_in_question)

            # save to txt file
            save_file = f'vis_auto_tagging/detect/{dataset}_detect_{version}.txt'
            f = open(save_file, 'w')
            for response in responses:
                f.write(response + '\n\n')
            f.close()
        elif mode == 'ground':
            print(f"Running {dataset}")
            if not os.path.exists(detected_key_fact_file):
                print(f"Please run the 'detect' mode for {dataset} first to get the detected key facts.")
                continue
            responses = grounding_facts_to_QA(fewshot_cot_file_path, detected_key_fact_file, instruction_for_grounding_in_answer, examples_for_grounding_in_answer)

            # save to txt file
            save_file = f'vis_auto_tagging/ground_v13/{dataset}_ground_{version}.txt'
            f = open(save_file, 'w')
            for response in responses:
                f.write(response + '\n\n')
            f.close()
