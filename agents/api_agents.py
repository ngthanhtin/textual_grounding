from utils.keys import API_KEYS
# gemini
import google.generativeai as genai
from google.generativeai.types import RequestOptions
from google.api_core import retry
# claude
import anthropic
# llama
import groq
from together import Together
# gpt4
from openai import OpenAI
import openai

from together import Together

import random, time
from tqdm import tqdm

def api_agent(llm_model, prompt, temperature=1.0):
    """
    prompt: fs + question + instruction
    """
    
    if 'gemini' in llm_model:
        genai.configure(api_key=API_KEYS['gemini'])
        model_config = {
            "temperature": temperature,
            }
        model = genai.GenerativeModel(llm_model, 
                                        generation_config=model_config
                                        )
        try:
            response = model.generate_content(prompt, request_options=RequestOptions(retry=retry.Retry(initial=10, multiplier=2, maximum=60, timeout=60)))
            return response.text
        except:
            return None
        
    elif 'claude' in llm_model:
        client = anthropic.Anthropic(api_key=API_KEYS['claude'])
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                temperature = temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except:
            return None
        
    elif 'gpt-4' in llm_model:
        client = OpenAI(
                api_key=API_KEYS['gpt4'],
            )
        try:
            response = client.chat.completions.create(
                        model=llm_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        n=1,
                        frequency_penalty=0,
                        presence_penalty=0,
                        max_tokens=10
                    )
            choices = response.choices
        
            completion_objs = [choice.message for choice in choices]
            completions = [
                completion.content for completion in completion_objs]

            return completions[0]
        except:
            return None
    elif llm_model == 'llama_together':
        # prompt = (
        #     "<|begin_of_text|>"                              # start of prompt
        #     "<|start_header_id|>user<|end_header_id|>"       # user header
        #     f"{question}"                                    # user input
        #     "<|eot_id|>"                                     #end of turn
        #     "<|start_header_id|>assistant<|end_header_id|>"  #assistant header
        # )
        client = Together(api_key=API_KEYS['together'])
        try:
            response = client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                messages=[{
                        "role": "user",
                        "content": prompt
                },],
                max_tokens=1024,
                temperature=temperature,
                repetition_penalty=1,
                stop=["<|eot_id|>","<|eom_id|>"],
                stream=True
            )
            
            return response.choices[0].message.content
        except:
            return None

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
                            temperature=temperature,
                        )
            response = response.choices[0].message.content
            return response
        except:
            return None
    elif llm_model == 'llama_sambanova_70b':
        client = openai.OpenAI(
            api_key=API_KEYS['sambanova'],
            base_url="https://api.sambanova.ai/v1",
        )
        try:
            response = client.chat.completions.create(
                model='Meta-Llama-3.1-70B-Instruct',
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                temperature=0.6, # Meta default 0.6
                top_p = 0.9, # Meta default 0.9
                max_tokens=1024
            )
            time.sleep(1)  # Pause execution for 2 seconds
            return response.choices[0].message.content
        except:
            return None
    elif llm_model == 'llama_sambanova_405b':
        client = openai.OpenAI(
            api_key=API_KEYS['sambanova'],
            base_url="https://api.sambanova.ai/v1",
        )
        try:
            response = client.chat.completions.create(
                model='Meta-Llama-3.1-405B-Instruct',
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                temperature=0.6, # Meta default
                top_p = 0.9, # Meta default
                max_tokens=1024
            )
            time.sleep(1)  # Pause execution for 2 seconds
            return response.choices[0].message.content
        except:
            return None
    elif llm_model == 'llama_sambanova_8b':
        client = openai.OpenAI(
            api_key=API_KEYS['sambanova'],
            base_url="https://api.sambanova.ai/v1",
        )
        try:
            response = client.chat.completions.create(
                model='Meta-Llama-3.1-8B-Instruct',
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                temperature=0.6, # Meta default
                top_p = 0.9, # Meta default
                max_tokens=1024
            )
            time.sleep(1)  # Pause execution for 2 seconds
            return response.choices[0].message.content
        except:
            return None
        
    elif llm_model == 'llama_sambanova_33_70b':
        client = openai.OpenAI(
            api_key=API_KEYS['sambanova'],
            base_url="https://api.sambanova.ai/v1",
        )
        try:
            response = client.chat.completions.create(
                model='Meta-Llama-3.3-70B-Instruct',
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                temperature=0.6, # Meta default
                top_p = 0.9, # Meta default
                max_tokens=1024
            )
            time.sleep(2)  # Pause execution for 2 seconds
            return response.choices[0].message.content
        except:
            return None
    
    elif llm_model == 'qwen25_coder_32b':
        try:
            client = openai.OpenAI(
            api_key=API_KEYS['sambanova'],
            base_url="https://api.sambanova.ai/v1",
            )
            
            messages = [
                {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]

            response = client.chat.completions.create(
                model='Qwen2.5-Coder-32B-Instruct',
                messages=messages,
                temperature =  0.7,
                top_p = 0.8,
                max_tokens = 1024
            )

            time.sleep(2)  # Pause execution for 2 seconds
            return response.choices[0].message.content
        except:
            return None
    elif llm_model == 'deepseek_r1':
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
            
            client = Together(api_key=API_KEYS['together'])
            response = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-R1",
                messages=messages,
                max_tokens=2048,
                temperature=0.6,
                top_p=0.95,
                top_k=50,
                repetition_penalty=1
            )
            
            return response.choices[0].message.content
        except:
            return None