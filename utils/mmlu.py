"""Response Parsing and Evaluation for various models"""
from typing import Dict
import random
random.seed(42)
import numpy as np
import re, json

# ----------- Process Multi-choice -------------
def parse_multi_choice_response(response, all_choices, index2ans):
    """
    Parse the prediction from the generated response.
    Return the predicted index e.g., A, B, C, D.
    """
    for char in [',', '.', '!', '?', ';', ':', "'"]:
        response = response.strip(char)
    response = " " + response + " " # add space to avoid partial match

    index_ans = True
    ans_with_brack = False
    candidates = []
    
    response = response.lower()
    all_choices = [choice.lower() for choice in all_choices]
            
    for choice in all_choices:  # e.g., (A) (B) (C) (D), (a), (b), (c), (d)
        if f'({choice})' in response:
            candidates.append(choice)
            ans_with_brack = True
        elif '{' + f'{choice}' + '}' in response:
            candidates.append(choice)
            ans_with_brack = True
            

    if len(candidates) == 0:
        for choice in all_choices: # e.g., A B C D
            if f' {choice} ' in response:
                candidates.append(choice)

    # if all above doesn't get candidates, check if the content is larger than 5 tokens and try to parse the example
    if len(candidates) == 0 and len(response.split()) > 5:
        for index, ans in index2ans.items():
            if ans.lower() in response.lower():
                candidates.append(index)
                index_ans = False # it's content ans.

    if len(candidates) == 0:  # still not get answer, randomly choose one.
        pred_index = random.choice(all_choices)
    elif len(candidates) > 1:
        start_indexes = []
        if index_ans:
            if ans_with_brack: 
                for can in candidates:
                    index = response.rfind(f'({can})')
                    start_indexes.append(index) # -1 will be ignored anyway
                # start_indexes = [generated_response.index(f'({can})') for can in candidates]
            else:
                for can in candidates:
                    index = response.rfind(f" {can} ")
                    start_indexes.append(index)
        else:
            for can in candidates:
                index = response.lower().rfind(index2ans[can].lower())
                start_indexes.append(index)
        # get the last one
        pred_index = candidates[np.argmax(start_indexes)]
    else: # if only one candidate, use it.
        pred_index = candidates[0]

    return pred_index

# ----------- Process Open -------------
def check_is_number(string):
    """
    Check if the given string a number.
    """
    try:
        float(string.replace(',', ''))
        return True
    except ValueError:
        # check if there's comma inside
        return False

def normalize_str(string):
    """
    Normalize the str to lower case and make them float numbers if possible.
    """
    # check if characters in the string

    # if number, numerize it.
    string = string.strip()

    is_number = check_is_number(string)

    if is_number:
        string = string.replace(',', '')
        string = float(string)
        # leave 2 decimal
        string = round(string, 2)
        return [string]
    else: # it's likely to be a string
        # lower it 
        string = string.lower()
        if len(string) == 1:
            return [" " + string, string + " "] # avoid trivial matches
        return [string]

def extract_numbers(string):
    """
    Exact all forms of numbers from a string with regex.
    """
    # Pattern for numbers with commas
    pattern_commas = r'-?\b\d{1,3}(?:,\d{3})+\b'
    # Pattern for scientific notation
    pattern_scientific = r'-?\d+(?:\.\d+)?[eE][+-]?\d+'
    # Pattern for simple numbers without commas
    pattern_simple = r'-?(?:\d+\.\d+|\.\d+|\d+\b)(?![eE][+-]?\d+)(?![,\d])'

    # Extract numbers with commas
    numbers_with_commas = re.findall(pattern_commas, string)
    # Extract numbers in scientific notation
    numbers_scientific = re.findall(pattern_scientific, string)
    # Extract simple numbers without commas
    numbers_simple = re.findall(pattern_simple, string)

    # Combine all extracted numbers
    all_numbers = numbers_with_commas + numbers_scientific + numbers_simple
    return all_numbers

def parse_open_response(response):
    """
    Parse the prediction from the generated response.
    Return a list of predicted strings or numbers.
    """
    # content = content.strip("\n").strip(".").strip(" ")
    def get_key_subresponses(response):
        key_responses = []
        response = response.strip().strip(".").lower()
        sub_responses = re.split(r'\.\s(?=[A-Z])|\n', response)
        indicators_of_keys = ['could be ', 'so ', 'is ',
                            'thus ', 'therefore ', 'final ', 'answer ', 'result ']
        key_responses = []
        for index, resp in enumerate(sub_responses):
            # if last one, accept it's an equation (the entire response can be just one sentence with equation)
            if index == len(sub_responses) - 1:
                indicators_of_keys.extend(['='])
            shortest_key_response = None # the shortest response that may contain the answer (tail part of the response)
            for indicator in indicators_of_keys:
                if indicator in resp:
                    if not shortest_key_response:
                        shortest_key_response = resp.split(indicator)[-1].strip()
                    else:
                        if len(resp.split(indicator)[-1].strip()) < len(shortest_key_response):
                            shortest_key_response = resp.split(indicator)[-1].strip()
                    # key_responses.append(resp.split(indicator)[1].strip())
            
            if shortest_key_response:
                # and it's not trivial
                if shortest_key_response.strip() not in [":", ",", ".", "!", "?", ";", ":", "'"]:
                    key_responses.append(shortest_key_response)
        if len(key_responses) == 0: # did not found any
            return [response]
        return key_responses
    # pdb.set_trace()
    key_responses = get_key_subresponses(response)

    pred_list = key_responses.copy() # keep the original string response
    for resp in key_responses:
        pred_list.extend(extract_numbers(resp))

    tmp_pred_list = []
    for i in range(len(pred_list)):
        tmp_pred_list.extend(normalize_str(pred_list[i]))
    pred_list = tmp_pred_list

    # remove duplicates
    pred_list = list(set(pred_list))

    return pred_list

# ----------- Evaluation -------------

def eval_multi_choice(gold_i, pred_i):
    """
    Evaluate a multiple choice instance.
    """
    correct = False
    # only they are exactly the same, we consider it as correct
    if isinstance(gold_i, list):
        for answer in gold_i:
            if answer == pred_i:
                correct = True
                break
    else: # gold_i is a string
        if gold_i == pred_i:
            correct = True
    return correct

def eval_open(gold_i, pred_i):
    """
    Evaluate an open question instance
    """
    correct = False
    if isinstance(gold_i, list):
        # use float to avoid trivial matches
        norm_answers = []
        for answer in gold_i:
            norm_answers.extend(normalize_str(answer))
    else:
        norm_answers = normalize_str(gold_i)
    for pred in pred_i: # pred is already normalized in parse response phase
        if isinstance(pred, str): # if it's a string, then find if ans in the pred_i
            for norm_ans in norm_answers:
                # only see if the string answer in the string pred
                if isinstance(norm_ans, str) and norm_ans in pred:
                    if not correct:
                        correct = True
                    break
        else: # it's a float number
            if pred in norm_answers:
                if not correct:
                    correct = True
                break
    return correct

# ----------- Batch Evaluation -------------
def evaluate(samples):
    """
    Batch evaluation for multiple choice and open questions.
    """
    pred_correct = 0
    judge_dict = dict()
    for sample in samples:
        gold_i = sample['answer']
        pred_i = sample['parsed_pred']
        if sample['question_type'] == 'multiple-choice':
            correct = eval_multi_choice(gold_i, pred_i)
        else: # open question
            correct = eval_open(gold_i, pred_i)

        if correct:
            judge_dict[sample['id']] = 'Correct'
            pred_correct += 1
        else:
            judge_dict[sample['id']] = 'Wrong'

    if len(samples) == 0:
        return {'acc': 0}
    return judge_dict, {'acc': pred_correct / len(samples)}



# ----------- Calculate Accuracy -------------
def calculate_ins_level_acc(results: Dict):
    """Calculate the instruction level accuracy for given Subject results"""
    acc = 0
    ins_num = 0
    for cat_results in results.values():
        acc += cat_results['acc'] * cat_results['num_example']
        ins_num += cat_results['num_example']
    if ins_num == 0:
        return 0
    return acc / ins_num

def parse_options(question):
    """
    return index to answer option
    """
    # Extract the answer options part using regular expression
    options_text = re.search(r"# Answer option: \[(.*?)\]", question).group(1)

    # Find each option and answer pair
    options = re.findall(r"([A-E])\)([^,]+)", options_text)

    # Convert the list of tuples into a dictionary
    answer_dict = {option: answer for option, answer in options}

    return answer_dict

######## END OF MMLU EVALUATORS ##########

def check_math_answer(answer, gt, verbose=False):
    acc = 0
    
    try:
        extracted_answer = answer.split('{')[-1].split('}')[0]
        extracted_answer = extracted_answer.replace(":", "").replace("*", "").replace("$", "").replace(",", "").replace("{", "").replace("}", "").replace("€", "").replace('%', '')
        extracted_answer = extracted_answer.strip()
        if float(gt) == float(extracted_answer):
            acc += 1
        
    except:
        extracted_answer = answer.split('{')[-1].split('}')[0]
        extracted_answer = extracted_answer.replace(":", "").replace("*", "").replace("$", "").replace(",", "").replace("{", "").replace("}", "").replace("€", "").replace('%', '')
        extracted_answer = extracted_answer.strip()
        
        pred_list = parse_open_response(extracted_answer)
        if gt in pred_list:
            acc += 1
        
    return acc

def check_gsm_hard_answer(answer, gt, verbose=False):
    acc = 0
    
    try:
        extracted_answer = answer.split('{')[-1].split('}')[0]
        extracted_answer = extracted_answer.replace(":", "").replace("*", "").replace("$", "").replace(",", "").replace("{", "").replace("}", "").replace("€", "").replace('%', '')
        extracted_answer = extracted_answer.strip()
        if round(float(gt), 1) == round(float(extracted_answer), 1):
            acc += 1
    except:
        extracted_answer = answer.split('{')[-1].split('}')[0]
        extracted_answer = extracted_answer.replace(":", "").replace("*", "").replace("$", "").replace(",", "").replace("{", "").replace("}", "").replace("€", "").replace('%', '')
        extracted_answer = extracted_answer.strip()
        
        pred_list = parse_open_response(extracted_answer)
        if gt in pred_list:
            acc += 1
        
    return acc

def compute_acc_gsm_plus(questions, answers, gts):
    # load original dataset
    def read_jsonl_file(file_path):
        with open(file_path, 'r') as file:
            data = [json.loads(line) for line in file]
        return data
    data = read_jsonl_file('../data/GSM_Plus/test.jsonl')

    perturb_dict = {}
    for row in data:
        question = row['question']
        perturbation_type = row['perturbation_type']
        
        if perturbation_type not in perturb_dict:
            perturb_dict[perturbation_type] = 0
        else:
            perturb_dict[perturbation_type] += 1
    print(perturb_dict)

    acc_perturb_dict = {k: 0 for k in perturb_dict.keys()}

    for row in data:
        question = row['question']
        perturbation_type = row['perturbation_type']

        for i, (generated_question, answer, gt) in enumerate(zip(questions, answers, gts)):
            if generated_question == question:
                acc_perturb_dict[perturbation_type] += check_math_answer(answer, gt)
                break
    
    for k, v in acc_perturb_dict.items():
        print(f'{k}: {v/perturb_dict[k]}')
        
def check_asdiv_answer(answer, gt, verbose=False):
    acc = 0
    try:
        extracted_answer = answer.split('{')[-1].split('}')[0]
        extracted_answer = extracted_answer.replace(":", "").replace("*", "").replace("$", "").replace(",", "").replace("{", "").replace("}", "").replace("€", "").replace('%', '')
        extracted_answer = extracted_answer.strip()
        if float(gt)-1 == float(extracted_answer):
            acc += 1
        elif float(extracted_answer) == float(gt) or \
            float(extracted_answer)*100 == float(gt) or \
                float(extracted_answer) == float(gt)*100:
            acc += 1
        else:
            if verbose:
                print("Answer 1: ", answer[-100:], 'GT: ', gt)
                print("====================================")
    except:
        extracted_answer = answer.split('{')[-1].split('}')[0]
        extracted_answer = extracted_answer.replace(":", "").replace("*", "").replace("$", "").replace(",", "").replace("{", "").replace("}", "").replace("€", "").replace('%', '')
        extracted_answer = extracted_answer.strip()
        
        pred_list = parse_open_response(extracted_answer)
        if gt in pred_list:
            acc += 1
        else:
            if str(int(gt)) in extracted_answer:
                acc += 1
            else:
                if verbose:
                    print("Answer 2: ", extracted_answer[-100:], 'GT: ', gt)
                    print("====================================")
    return acc

def check_aqua_answer(question, answer, gt, verbose=False):
    acc = 0
    index2ans = parse_options(question)
    # remove ' in index2ans
    index2ans = {key: value.replace("'", "") for key, value in index2ans.items()}
    
    # all_choices = list(index2ans.keys())
    # pred_index = parse_multi_choice_response(answer, all_choices, index2ans)
    
    gt_number  = index2ans[gt]
    
    try:
        extracted_answer = answer.split('{')[-1].split('}')[0]
        if gt.upper() in extracted_answer or gt_number in extracted_answer:
            acc += 1
    except:
        
        if 'The closest answer option is' in answer:
            extracted_answer = answer.split('The closest answer option is')[-1]
        elif'The correct answer is' in answer:
            extracted_answer = answer.split('The correct answer is')[-1]
        elif 'Therefore, the answer is' in answer:
            extracted_answer = answer.split('Therefore, the answer is')[-1]
        elif 'Therefore the answer is' in answer:
            extracted_answer = answer.split('Therefore the answer is')[-1]
        else:
            extracted_answer = answer[-200:]
        # if gt.upper() == label or gt_number in extracted_answer:
        #     total_acc += 1
        # else:
        pattern = r"(?i)([A-G])\)?[\s-]*\{?([^\{\}\(\)]+?)\}?(?=\s*[\(\{\[]?[A-G]\)?]|$)"
        matches = re.findall(pattern, extracted_answer)

        # Loop through matches and format them
        for label, extracted_answer in matches:
            if gt.upper() == label or gt_number in extracted_answer:
                acc += 1
                break
                    
    return acc


def check_bool_answer(answer, gt):
    acc = 0
    try:
        answer = answer.split('{')[1].split('}')[0]
    except:
        try:
            if 'the answer is no' in answer.lower():
                if bool(gt) == False:
                    acc += 1
                    return acc
            if 'the answer is yes' in answer.lower():
                if bool(gt) == True:
                    acc += 1
                    return acc
            if 'yes,' in answer.lower():
                if bool(gt) == True:
                    acc += 1
                    return acc
            if 'no,' in answer.lower():
                if bool(gt) == False:
                    acc += 1
                    return acc
            if any(x in answer.lower() for x in [' no ', ' no.', ' false ', 'false.', ' 0 ', ' 0.']):
                if bool(gt) == False:
                    acc += 1
                    return acc
            elif any(x in answer.lower() for x in [' yes ', ' yes.', ' true ', 'true.', ' 1 ', ' 1.']):
                if bool(gt) == True:
                    acc += 1
                    return acc
        except:
            return 0
    
    if answer.lower() in ['yes', 'true', '1']:
        answer = True
    elif answer.lower() in ['no', 'false', '0']:
        answer = False
    if bool(answer) == bool(gt):
        acc += 1
        
    return acc

def check_exact_match_answer(answer, gt, verbose=False):
    """
    works for date, wikimultihopQA
    """
    acc = 0
    conclusion = answer.split('{')[-1].split('}')[0]
            
    if conclusion.lower() == gt.lower():
        acc += 1
    else:
        if  gt.lower() in answer.lower():
            acc += 1
        else:
            if verbose:
                print("Answer: ", answer[-100:], 'GT: ', gt)
                print("====================================")
    
    return acc

def check_multiple_choice_answer(question, answer, gt, verbose=False):
    """
    works for ['logical_deduction_seven_objects', 'reasoning_about_colored_objects', 'commonsenseQA']
    """
    
    def extract_options_to_dict(text):
        # Regular expression to match the pattern of options
        pattern = r"\(([A-F])\)\s+(.+)"
        
        # Find all matches in the text
        matches = re.findall(pattern, text)
        
        # Initialize a dictionary to store the options
        options_dict = {}
        
        # Loop through matches and populate the dictionary
        for label, description in matches:
            options_dict[label] = description.strip()

        return options_dict

    acc = 0
    options_dict = extract_options_to_dict(question)

    if 'Answer: ' in answer:
        answer = answer.split('Answer: ')[-1].strip()
    
    if len(answer) < 10: # Sometimes it answers the option directly.
        if gt.lower() in answer.lower():
            acc += 1
            return acc
        
    extracted_answer = answer.split('{')[-1].split('}')[0]    
    if extracted_answer == answer: # can not extract
        extracted_answer = answer.split('(')[-1].split(')')[0]
        if extracted_answer == answer: # can not extract  
            if 'The closest answer option is' in answer:
                extracted_answer = answer.split('The closest answer option is')[-1]
            elif'The correct answer is' in answer:
                extracted_answer = answer.split('The correct answer is')[-1]
            elif 'Therefore, the answer is' in answer:
                extracted_answer = answer.split('Therefore, the answer is')[-1]
            elif 'Therefore the answer is' in answer:
                extracted_answer = answer.split('Therefore the answer is')[-1]
            else:
                extracted_answer = answer[-200:]
            
            # check if description in the extracted answer
            extracted_answer = extracted_answer.replace("*", "")
            is_exists = False
            for option, description in options_dict.items():
                if description.lower() in extracted_answer.lower():
                    acc += 1
                    is_exists = True
                    break
            if is_exists:
                return acc
            
            pattern = r"(?i)([A-G])\)?[\s-]*\{?([^\{\}\(\)]+?)\}?(?=\s*[\(\{\[]?[A-G]\)?]|$)"
            matches = re.findall(pattern, extracted_answer)

            # Loop through matches and format them
            for label, extracted_answer in matches:
                if gt.upper() == label:
                    acc += 1
                else:
                    if verbose:
                        print('Answer: ', answer[-200:], 'GT: ', gt)
                        print('------------------------------------')
            
        else:
            if gt.lower() in extracted_answer.lower():
                acc += 1
            else:
                if verbose:
                    print("Answer: ", extracted_answer[-100:], 'GT: ', gt)
                    print("====================================")
    else:
        if gt.lower() in extracted_answer.lower():
            acc += 1
        else:
            if verbose:
                print("Answer: ", extracted_answer[-100:], 'GT: ', gt)
                print("====================================")
    
    return acc


def check_drop_answer(answer, gt, verbose=False):
    
    try:
        extracted_answer = answer.split('{')[-1].split('}')[0]
        extracted_answer = extracted_answer.replace(":", "").replace("*", "").replace("$", "").replace(",", "").replace("{", "").replace("}", "").replace("€", "").replace('%', '')
        extracted_answer = extracted_answer.strip()
        for _gt in gt:
            if float(_gt) == float(extracted_answer):
                return 1
        # if float(_gt) == float(extracted_answer):
        #     return 1
        
    except:
        extracted_answer = answer.split('{')[-1].split('}')[0]
        extracted_answer = extracted_answer.replace(":", "").replace("*", "").replace("$", "").replace(",", "").replace("{", "").replace("}", "").replace("€", "").replace('%', '')
        extracted_answer = extracted_answer.strip()
        
        pred_list = parse_open_response(extracted_answer)
    
        for _gt in gt:
            if _gt in pred_list:
                return 1
            
    return 0

def check_squad_answer(answer, gt):
    # remove tag <fact> in the answer
    answer = re.sub(r'</?fact\d+>', '', answer)
    
    if gt in answer or answer in gt:
        return 1
    
    return 0

def check_medQA_answer(question, answer, gt):
    # remove tag <fact> in the answer
    answer = re.sub(r'</?fact\d+>', '', answer)
    gt_option = gt[0]
    gt_text = gt[1]
    
    is_correct = check_multiple_choice_answer(question, answer, gt_option)
    if is_correct == 0:
        if gt_text.lower() in answer.lower() or answer.lower() in gt_text.lower():
            return 1
        else:
            return 0
    else:
        return 1