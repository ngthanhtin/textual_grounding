# from utils.keys import API_KEYS
# gemini
import google.generativeai as genai
from google.generativeai.types import RequestOptions
from google.api_core import retry
# claude
import anthropic
# from anthropic import MessageCreateParamsNonStreaming
# from anthropic import Request
# llama
import groq
# from together import Together
# gpt4
from openai import OpenAI
import openai
import os
import time
import logging
import csv


import random, json
random.seed(0)


def prepare_batch_input(llm_model, ids, prompts, temperature=1.0, max_tokens=1024, batch_output_file='batch_output.jsonl'):
    tasks = []
    
    if 'gpt-4' in llm_model:
        for index, prompt in zip(ids, prompts):
            
            task = {
                "custom_id": f"{index}",
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

def combine_results_to_csv(batch_input_file, batch_result_file, output_csv_file):
    """Combines batch input and results into a single CSV file."""
    id_prompt_map = {}
    
    # Read batch input to map custom_id to prompt
    with open(batch_input_file, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            custom_id = entry.get('custom_id')
            try:
                prompt = entry['body']['messages'][1]['content']  # Assuming prompt is the second message
            except (KeyError, IndexError) as e:
                logging.error(f"Error extracting prompt for custom_id {custom_id}: {e}")
                prompt = "N/A"
            id_prompt_map[custom_id] = prompt

    id_answer_map = {}
    
    # Read batch results to map custom_id to answer
    with open(batch_result_file, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            custom_id = entry.get('custom_id')
            # Corrected path to access 'choices'
            try:
                answer = entry['response']['body']['choices'][0]['message']['content'].strip()
            except (KeyError, IndexError) as e:
                logging.error(f"Error extracting answer for custom_id {custom_id}: {e}")
                answer = "N/A"  # or handle it as you see fit
            id_answer_map[custom_id] = answer

    # Combine into CSV
    with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'prompt', 'answer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for custom_id, prompt in id_prompt_map.items():
            answer = id_answer_map.get(custom_id, "N/A")
            writer.writerow({'id': custom_id, 'prompt': prompt, 'answer': answer})

    logging.info(f"Combined results saved to {output_csv_file}")
    
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def batch_api_agent(
    llm_model, 
    ids, 
    prompts, 
    temperature=1.0, 
    max_tokens=1024, 
    batch_output_file='batch_input.jsonl', 
    batch_results_file='results.jsonl',
    poll_interval=10,  # Seconds between status checks
    max_wait_time=3600  # Maximum wait time in seconds (e.g., 1 hour)
):
    try:
        combined_csv_file_path = batch_results_file.replace('.jsonl', '.csv')
        
        # Prepare the batch input file
        prepare_batch_input(llm_model, ids, prompts, temperature, max_tokens, batch_output_file)
        logging.info(f"Batch input file created at: {batch_output_file}")

        # Initialize OpenAI client
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")
        
        client = OpenAI()
        logging.info("OpenAI client initialized.")

        if 'gpt-4' in llm_model:
            # Upload the batch input file
            with open(batch_output_file, "rb") as f:
                batch_file = client.files.create(file=f, purpose="batch")
            logging.info(f"Batch input file uploaded with file ID: {batch_file.id}")

            # Create the batch job
            batch_job = client.batches.create(
                input_file_id=batch_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h"
            )
            logging.info(f"Batch job created with job ID: {batch_job.id}")

            # Poll for job status
            start_time = time.time()
            while True:
                job_status = client.batches.retrieve(batch_job.id)
                logging.info(f"Batch job status: {job_status.status}")

                if job_status.status == "completed":
                    if not job_status.output_file_id:
                        raise ValueError("Batch job succeeded but no output_file_id found.")
                    result_file_id = job_status.output_file_id
                    logging.info(f"Batch job succeeded. Output file ID: {result_file_id}")
                    break
                elif job_status.status == "failed":
                    raise RuntimeError(f"Batch job failed: {job_status.error_message}")
                else:
                    logging.info(f"Batch job is {job_status.status}. Waiting for {poll_interval} seconds before next check.")

                # Check for timeout
                elapsed_time = time.time() - start_time
                if elapsed_time > max_wait_time:
                    raise TimeoutError("Batch job did not complete within the maximum wait time.")

                time.sleep(poll_interval)

            # Download the result file
            result = client.files.content(result_file_id).content
            with open(batch_results_file, 'wb') as file:
                file.write(result)
            logging.info(f"Batch results saved to: {batch_results_file}")
            
            combine_results_to_csv(batch_output_file, batch_results_file, combined_csv_file_path)

        elif 'gemini' in llm_model:
            pass
        
        elif 'claude' in llm_model:
            # client = anthropic.Anthropic(api_key=API_KEYS['claude'])
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
    except Exception as e:
        logging.error(f"An error occurred in batch_api_agent: {str(e)}")
        raise  # Re-raise the exception after logging