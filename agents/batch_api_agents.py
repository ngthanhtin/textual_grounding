from utils.keys import API_KEYS
# gemini
import google.generativeai as genai
from google.generativeai.types import RequestOptions
from google.api_core import retry
# claude
import anthropic
# from anthropic.types.beta.message_create_params import MessageCreateParamsNonStreaming
# from anthropic.types.beta.messages.batch_create_params import Request
# llama
import groq
from together import Together
# gpt4
from openai import OpenAI
import openai

import random, json, os
# random.seed(0)

def prepare_batch_input(llm_model, ids, prompts, temperature=1.0, max_tokens=1024, batch_output_file='batch_output.jsonl'):
    tasks = []
    
    if 'gpt-4' in llm_model:
        for index, prompt in zip(ids, prompts):
            
            task = {
                "custom_id": f"task-{index}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    # This is what you would have in your Chat Completions API call
                    "model": llm_model,
                    "temperature": temperature,
                    "messages": [
                        {
                            "role": "system",
                            "content": ""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": max_tokens
                }
            }
            
            tasks.append(task)

        with open(batch_output_file, 'w') as f:
            for item in tasks:
                f.write(json.dumps(item) + '\n')
        
    elif 'gemini' in llm_model:
        pass
    elif 'claude' in llm_model:
        for index, prompt in zip(ids, prompts):
            tasks = [Request(
                custom_id=f"task-{index}",
                params=MessageCreateParamsNonStreaming(
                model="claude-3-5-sonnet-20240620",
                max_tokens=max_tokens,
                messages=[
                    {
                    "role": "user",
                    "content": prompt,
                    }
                    ]
            ))]
            
            tasks.append(task)
    
    return tasks
    
def batch_api_agent(llm_model, ids, prompts, temperature=1.0, max_tokens=1024, batch_output_file='batch_input.jsonl', result_file='results.jsonl'):
    
    # Creating an array of json tasks
    # check if batch_output_file exists
    if not os.path.exists(batch_output_file):
        tasks = prepare_batch_input(llm_model, ids, prompts, temperature, max_tokens, batch_output_file)
    else: # read jsonl file into a list
        tasks = [] 
        with open(batch_output_file, 'r') as file:
            for line in file:
                json_obj = json.loads(line)  # Parse the JSON data from the line
                tasks.append(json_obj)
        
    if 'gpt-4' in llm_model:
        client = OpenAI(
                api_key=API_KEYS['gpt4'],
            )
        
        batch_file = client.files.create(file=open(batch_output_file, "rb"), purpose="batch")
        
        batch_job = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
        )
        print("Batch job id:", batch_job.id)
        
    elif 'gemini' in llm_model:
        pass
    
    elif 'claude' in llm_model:
        client = anthropic.Anthropic(api_key=API_KEYS['claude'])
        message_batch = client.beta.messages.batches.create(
        requests=tasks
        )
        
        print(message_batch)
        message_batch = client.beta.messages.batches.retrieve("msgbatch_01HkcTjaV5uDC8jWR4ZsDV8d",)
        
        # Stream results file in memory-efficient chunks, processing one at a time
        for result in client.beta.messages.batches.results(message_batch.id):
            result = result.custom_id
            with open(result_file, 'a') as file:
                file.write(result)