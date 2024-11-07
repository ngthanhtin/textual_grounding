import argparse

def get_common_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--llm_model', type=str, default='gemini', help='The language model to query', choices=['gemini-1.5-pro-002', 'gemini-1.5-flash-002', 'claude', 'gpt-4o-2024-08-06', 'gpt-4o-mini-2024-07-18', 'llama_transformer', 'llama_groq', 'llama_together'])
    arg_parser.add_argument('--temperature', type=float, default=1.0, help='The temperature to use for the language model')
    arg_parser.add_argument('--dataset', type=str, default='GSM8K', help='The dataset to query', choices=['GSM8K', 'StrategyQA', 'p_GSM8K', 'AQUA', 'MultiArith', 'ASDiv', 'SVAMP', 'commonsenseQA', 'wikimultihopQA', 'date', 'sports', 'reclor', 'CLUTRR', 'object_counting', 'navigate', 'causal_judgement', 'logical_deduction_three_objects', 'logical_deduction_five_objects', 'logical_deduction_seven_objects', 'reasoning_about_colored_objects', 'GSM_Plus', 'GSM_IC', 'spartQA', 'last_letter_2', 'last_letter_4', 'coin', 'word_sorting', 'tracking_shuffled_objects_seven_objects', 'gpqa', 'GSM8K_Hard'])
    arg_parser.add_argument('--prompt_used', type=str, default='fs_inst', help='The prompt used to query the language model', choices=['zs', 'fs', 'fs_inst'])
    arg_parser.add_argument('--answer_mode', type=str, default='da', help='The answer mode', choices=['da', 'cot', 'grounding_cot'])
    arg_parser.add_argument('--save_answer', action='store_true')
    arg_parser.add_argument('--data_mode', type=str, default='longest', help='The data mode', choices=['random', 'longest'])
    arg_parser.add_argument('--batch_request', action='store_true')
    
    return arg_parser