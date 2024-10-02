import gradio as gr
from tqdm import tqdm
from utils.keys import API_KEYS
import anthropic
import google.generativeai as genai
from google.generativeai.types import RequestOptions
from google.api_core import retry

# Mock LLM client for now
def mock_llm_response(prompt, llm_model='gemini'):
    if llm_model == 'gemini':
        genai.configure(api_key=API_KEYS['gemini'])
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        try:
            response = model.generate_content(prompt, request_options=RequestOptions(retry=retry.Retry(initial=10, multiplier=2, maximum=60, timeout=60)))
            return response.text
        except:
            return "Failed to generate response"
    if llm_model == 'claude':
        client = anthropic.Anthropic(api_key=API_KEYS['claude'])
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except:
            return "Failed to generate response"

# Step 1: Function to extract key phrases
def step_1_extract_phrases(question):
    # Create a mock response similar to LLM output
    extract_prompt = f"Identify and list key phrases from the following question that are crucial to providing a comprehensive answer, format each with a single index in square bracket at the end of each phrase.\n{question}"
    response = mock_llm_response(extract_prompt)
    
    # Return the response (which should be editable by the user)
    return response

# Step 2: Function to generate answer with the edited phrases
def step_2_generate_answer(question, formatted_phrases):
    fewshot_prompt_path = f"prompt/GSM8K/fewshot_key_phrases_v2.txt"
    few_shot_prompt = open(fewshot_prompt_path, 'r').read()
    answer_prompt = f"{few_shot_prompt}\n{question}\n{formatted_phrases}\nUse the indexed phrases to construct your answer, referencing the phrases as needed."

    # Mock LLM response for the answer generation
    response = mock_llm_response(answer_prompt)

    return response

# Gradio interface
def create_interface():
    with gr.Blocks() as demo:
        # Step 1: Extract phrases from the question
        question_input = gr.Textbox(label="Input Question", placeholder="Enter the question here", lines=2)
        extracted_phrases = gr.Textbox(label="Extracted Phrases (editable)", placeholder="Key phrases will appear here", lines=5)

        # Button for Step 1
        extract_btn = gr.Button("Step 1: Extract Key Phrases")
        
        # Step 2: Generate the answer based on the formatted phrases
        final_answer = gr.Textbox(label="Generated Answer", placeholder="The final answer will appear here", lines=5)

        # Button for Step 2
        generate_btn = gr.Button("Step 2: Generate Answer")

        # Step 1: On button click for extraction
        extract_btn.click(step_1_extract_phrases, inputs=question_input, outputs=extracted_phrases)
        
        # Step 2: On button click for answer generation (with editable phrases)
        generate_btn.click(step_2_generate_answer, inputs=[question_input, extracted_phrases], outputs=final_answer)
    
    return demo

# Run the Gradio demo
demo = create_interface()
demo.launch()


# Janet’s ducks lay 16 eggs per day. She eats three for breakfast every morning and bakes muffins for her friends every day with four. She sells the remainder at the farmers' market daily for $2 per fresh duck egg. How much in dollars does she make every day at the farmers' market?