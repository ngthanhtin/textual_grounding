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

import anthropic
from anthropic.types.beta.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.beta.messages.batch_create_params import Request


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
        # Create a list of requests instead of a dictionary
        requests = []
        for index, prompt in zip(ids, prompts):
            request = {
                "custom_id": f"{index}",
                "params": {
                    "model": llm_model,
                    "max_tokens": max_tokens,
                    "messages": [{
                        "role": "user",
                        "content": prompt,
                    }]
                }
            }
            requests.append(request)

        # Save the requests to file if needed
        with open(batch_output_file, 'w') as f:
            json.dump(requests, f)
            
        return requests

def process_claude_batch_results(batch_id: str, client: anthropic.Anthropic, 
                               output_csv_file: str) -> None:
    results_data = []
    
    # Stream results and process each result
    for result in client.beta.messages.batches.results(batch_id):
        result_entry = {
            'id': result.custom_id,
            'prompt': '',  # Will need to be filled in from original prompts
            'answer': ''
        }
        
        if result.result.type == "succeeded":
            # Extract the assistant's message content
            content = result.result.message.content
            if isinstance(content, list):
                # Combine all text content if there are multiple parts
                result_entry['answer'] = ' '.join(
                    part.text for part in content 
                    if hasattr(part, 'text')
                )
            else:
                result_entry['answer'] = str(content)
        else:
            result_entry['answer'] = f"Error: {result.result.type}"
            
        results_data.append(result_entry)
    
    # Write results to CSV
    with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'prompt', 'answer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in results_data:
            writer.writerow(entry)

def combine_results_to_csv(batch_input_file, batch_result_file, output_csv_file):
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
        tasks = prepare_batch_input(llm_model, ids, prompts, temperature, max_tokens, batch_output_file)
        logging.info(f"Batch input file created at: {batch_output_file}")

        if 'gpt-4' in llm_model:
            # Initialize OpenAI client
            openai.api_key = os.getenv('OPENAI_API_KEY')
            if not openai.api_key:
                raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")
            client = OpenAI()
            logging.info("OpenAI client initialized.")
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
            try:
                client = anthropic.Anthropic()
                # Create batch request
                print(tasks)
                print()
                message_batch = client.beta.messages.batches.create(requests=tasks)
                message_id = message_batch.id
                
                logging.info(f"Created batch with ID: {message_id}")
                

                # Poll for batch completion
                wait_time = 0
                while wait_time < max_wait_time:
                    message_batch = client.beta.messages.batches.retrieve(message_id)
                    
                    if message_batch.processing_status == "completed":
                        break
                    elif message_batch.processing_status == "failed":
                        raise Exception(f"Batch processing failed: {message_batch.error}")
                    
                    time.sleep(poll_interval)
                    wait_time += poll_interval
                    logging.info(f"Batch Status: {message_batch.processing_status} - Time elapsed: {wait_time}s")
                
                if wait_time >= max_wait_time:
                    raise TimeoutError(f"Batch processing did not complete within {max_wait_time} seconds")
                
                # Process results
                with open(batch_results_file, 'w') as file:
                    for result in client.beta.messages.batches.results(message_id):
                        match result.result.type:
                            case "succeeded":
                                logging.info(f"Success for {result.custom_id}")
                                file.write(f"SUCCESS\t{result.custom_id}\t{result.result.message.content}\n")
                            case "errored":
                                error_type = result.result.error.type
                                error_message = result.result.error.message
                                if error_type == "invalid_request":
                                    logging.error(f"Validation error for {result.custom_id}: {error_message}")
                                else:
                                    logging.error(f"Server error for {result.custom_id}: {error_message}")
                                file.write(f"ERROR\t{result.custom_id}\t{error_type}: {error_message}\n")
                            case "expired":
                                logging.warning(f"Request expired for {result.custom_id}")
                                file.write(f"EXPIRED\t{result.custom_id}\n")
            except Exception as e:
                logging.error(f"Error processing batch: {str(e)}")
                raise 

            logging.info(f"Batch results saved to: {batch_results_file}")
            
            process_claude_batch_results(batch_output_file, batch_results_file, combined_csv_file_path)
        # elif 'claude' in llm_model:
        #     client = anthropic.Anthropic()
            
        #     # Prepare batch requests
        #     tasks = prepare_batch_input(llm_model, ids, prompts, temperature, max_tokens)
            
        #     # Create batch
        #     message_batch = client.beta.messages.batches.create(requests=tasks)
        #     batch_id = message_batch.id
        #     logging.info(f"Created Claude batch with ID: {batch_id}")
            
        #     # Poll for completion
        #     start_time = time.time()
        #     while True:
        #         batch_status = client.beta.messages.batches.retrieve(batch_id)
        #         logging.info(f"Batch status: {batch_status.processing_status}")
                
        #         if batch_status.processing_status == "succeeded":
        #             logging.info("Batch processing completed")
        #             break
                    
        #         # Check for timeout
        #         if time.time() - start_time > max_wait_time:
        #             raise TimeoutError("Batch processing exceeded maximum wait time")
                
        #         time.sleep(poll_interval)
            
        #     # Process results
        #     output_csv_file = f"claude_batch_results_{batch_id}.csv"
        #     process_claude_batch_results(batch_output_file, batch_results_file, combined_csv_file_path)
        #     logging.info(f"Results saved to {output_csv_file}")
    except Exception as e:
        logging.error(f"An error occurred in batch_api_agent: {str(e)}")
        raise  # Re-raise the exception after logging