import re, json
from collections import Counter

index_2_color_map = {
    1: "#FF5733",  # Red
    2: "#33FF57",  # Green
    3: "#3357FF",  # Blue
    4: "#FF33A1",  # Pink
    5: "#FFA533",  # Orange
    6: "#33FFF3",  # Cyan
    7: "#FFDD33",  # Golden Yellow
    8: "#8D33FF",  # Purple
    9: "#33FF8D",  # Mint Green
    10: "#FF335E",  # Deep Rose
    11: "#3378FF",  # Light Blue
    12: "#FFB833",  # Amber
    13: "#FF33F5",  # Magenta
    14: "#75FF33",  # Lime Green
    15: "#33C4FF",  # Sky Blue
    16: "#FF8633",  # Deep Orange
    17: "#C433FF",  # Violet
    18: "#33FFB5",  # Aquamarine
    19: "#FF336B",  # Bright Pink
}

char_2_color_map = {
    'a': "#FF5733",  # Red
    'b': "#33FF57",  # Green
    'c': "#3357FF",  # Blue
    'd': "#FF33A1",  # Pink
    'e': "#FFA533",  # Orange
    'f': "#33FFF3",  # Cyan
    'g': "#FFDD33",  # Coral Red
    'h': "#8D33FF",  # Purple
    'i': "#33FF8D",  # Mint Green
    'j': "#FF335E",  # Deep Rose
    'k': "#3378FF",  # Light Blue
    'l': "#FFB833",  # Amber
    'm': "#FF33F5",  # Magenta
    'n': "#75FF33",  # Lime Green
    'o': "#33C4FF",  # Sky Blue
    'p': "#FF8633",  # Deep Orange
    'q': "#C433FF",  # Violet
    'r': "#33FFB5",  # Aquamarine
    's': "#FF336B",  # Bright Pink
}

char_2_color_map = {
    'fact1': "#FF5733",  # Red
    'fact2': "#33FF57",  # Green
    'fact3': "#3357FF",  # Blue
    'fact4': "#FF33A1",  # Pink
    'fact5': "#FFA533",  # Orange
    'fact6': "#33FFF3",  # Cyan
    'fact7': "#FFDD33",  # Coral Red
    'fact8': "#8D33FF",  # Purple
    'fact9': "#33FF8D",  # Mint Green
    'fact10': "#FF335E",  # Deep Rose
    'fact11': "#3378FF",  # Light Blue
    'fact12': "#FFB833",  # Amber
    'fact13': "#FF33F5",  # Magenta
    'fact14': "#75FF33",  # Lime Green
    'fact15': "#33C4FF",  # Sky Blue
    'fact16': "#FF8633",  # Deep Orange
    'fact17': "#C433FF",  # Violet
    'fact18': "#33FFB5",  # Aquamarine
    'fact19': "#FF336B",  # Bright Pink
}

def read_jsonl_file(filepath):
    data = [] 
    with open(filepath, 'r') as file:
        for line in file:
            json_obj = json.loads(line)  # Parse the JSON data from the line
            data.append(json_obj)  # Add the parsed JSON object to a list
    return data

# Function to replace tags with colored tags
def add_color_to_tags(text):
    # Iterate over the tag-color mappings
    for tag, color in char_2_color_map.items():
        # Regex to find the tag and replace it with the same tag having a color attribute
        text = re.sub(f'<{tag}>', f'<{tag} style="background-color: {color};">', text)
        text = re.sub(f'</{tag}>', f'</{tag}>', text)  # Closing tags remain unchanged
    return text

# Function to extract and compare text segments from tags
def calculate_iou(original_text, reformulated_text):
    # Extract tagged segments from both texts
    # original_tags = re.findall(r'<([abcde])>(.*?)<\/\1>', original_text)
    # reformulated_tags = re.findall(r'<([abcde])>(.*?)<\/\1>', reformulated_text)
    original_tags = re.findall(r'<(fact\d+)>(.*?)<\/\1>', original_text)
    reformulated_tags = re.findall(r'<(fact\d+)>(.*?)<\/\1>', reformulated_text)
    
    # Convert lists to dictionaries
    original_dict = {tag: text.strip() for tag, text in original_tags}
    reformulated_dict = {tag: text.strip() for tag, text in reformulated_tags}

    # Compute overlaps and unions for IoU
    ious = []
    for tag in original_dict:
        if tag in reformulated_dict:
            original_segment = original_dict[tag]
            reformulated_segment = reformulated_dict[tag]
            # Compute overlap (minimum of possible overlaps)
            overlap = len(set(original_segment.split()).intersection(set(reformulated_segment.split())))
            # Compute union
            union = len(set(original_segment.split()).union(set(reformulated_segment.split())))
            # Compute IoU
            iou = overlap / union if union != 0 else 0
            ious.append(iou)
    
    # Return average IoU if there are any IoUs calculated
    return sum(ious) / len(ious) if ious else 0, original_tags, reformulated_tags

# Function to extract parts of the text based on headers
def extract_parts_1(text):
    # Find the "Reformatted Question" and "Answer" sections
    question_match = re.search(r"Reformatted Question:(.*?)\nAnswer:", text, re.S)
    answer_match = re.search(r"Answer:(.*)", text, re.S)

    # Extracting text for each part
    if question_match:
        question_text = question_match.group(1).strip()
    else:
        question_match = re.search(r"Reformatted Question:(.*?)Answer:", text, re.S)
        answer_match = re.search(r"Answer:(.*)", text, re.S)
        
        if question_match:
            question_text = question_match.group(1).strip()
        else:
            question_text = "Question not found"
    
    if answer_match:
        answer_text = answer_match.group(1).strip()
    else:
        answer_text = "Answer not found"

    return question_text, answer_text

def count_tags(text):
    # Find all the tags using a regular expression
    tags = re.findall(r'<([a-z])>', text)
    
    # Count the occurrences of each tag using Counter
    tag_counts = Counter(tags)
    
    return tag_counts


def retrieve_gts(data_path, ids, dataset):
    """
    data_path: path to the whole data file
    ids: ids of the predictions (list)
    dataset: which dataset to retrieve the ground truth
    """
    if 'jsonl' in data_path:
        data = read_jsonl_file(f"{data_path}")
    else:
        with open(f"{data_path}", 'r') as file:
            data = json.load(file)
            
    # read gt
    gts = []
    if dataset in ['coin', 'last_letter_2', 'last_letter_4', 'GSM8K_Hard']:
        for id in ids:
            for i, temp in enumerate(data):
                if id == i:
                    # print(temp['new_question'], id, temp['answer'])
                    # exit()
                    gt = temp['answer']
                    if dataset == 'coin':
                        if gt == 'yes':
                            gt = True
                        else:
                            gt = False
                    gts.append(gt)
        return gts
    
    if dataset in ['GSM_Plus', 'GSM_IC']:
        if dataset == 'GSM_IC':
            length = 583 # 370: 2 step, 583: mstep
            questions = [x['new_question'] for x in data if len(x["new_question"]) >= length]
            answers = [x['answer'] for x in data if len(x["new_question"]) >= length]
            data = [{'new_question': q, 'answer': a} for q, a in zip(questions, answers)]
        num_cannot_convert = 0
        num_none = 0
        for id in ids:
            for i, temp in enumerate(data):
                if id == i:
                    # print(temp['new_question'], id, temp['answer'])
                    # exit()
                    gt = temp['answer']
                    if temp['answer'] == 'None':
                        gts.append(None)
                        num_none += 1
                    else:
                        try:
                            gts.append(float(gt))
                        except:
                            num_cannot_convert += 1
                            gts.append(None)
                            num_none += 1
        print(num_none)
        print(num_cannot_convert)
        # exit()
        
        return gts
    
    for id in ids:
        for temp in data:
            if dataset == 'squad':
                if temp['id'] == id:
                    gt = temp['answer']
                    gts.append(gt)
            if dataset in ['drop_break', 'drop_cencus']:
                if temp['id'] == id:
                    gt = temp['answer'][0][0]
                    gts.append(float(gt))
            if dataset == 'p_GSM8K':
                if temp['index'] == id:
                    gt = temp['answer']
                    gts.append(float(gt))
            elif dataset == 'wikimultihopQA':
                if temp['_id'] == id:
                    gt = temp['answer']
                    gts.append(gt)
            elif dataset == 'spartQA':
                if temp['id'] == id:
                    gt = temp['answer']
                    if gt == 0:
                        gt = 'A'
                    elif gt == 1:
                        gt = 'B'
                    elif gt == 2:
                        gt = 'C'
                    elif gt == 3:
                        gt = 'D'
                    gts.append(gt)
            elif dataset == 'reclor':
                if temp['id_string'] == id:
                    gt = temp['label']
                    if gt == 0:
                        gt = 'A'
                    elif gt == 1:
                        gt = 'B'
                    elif gt == 2:
                        gt = 'C'
                    elif gt == 3:
                        gt = 'D'
                    gts.append(gt)
            elif dataset == 'commonsenseQA':
                if temp['id'] == id:
                    gt = temp['answerKey']
                    gts.append(gt)
            else:
                if temp['id'] == id:
                    gt = temp['answer']
                    if dataset in ['GSM8K', 'MultiArith', 'SVAMP']:
                        gt = gt.split('####')[1].strip()
                        if ',' in gt:
                            gt = gt.replace(',', '')
                        gts.append(float(gt))
                    if dataset == 'CLUTRR':
                        gt = gt.split('####')[1].strip()
                        gts.append(gt)
                    if dataset == 'date':
                        gt = gt.split('####')[1].strip()
                        gts.append(gt)
                    if dataset == 'ASDiv':
                        #if gt is list, convert it to string
                        if type(gt) == list:
                            gt = gt[0]
                        gt = gt.replace(',', '')
                        gts.append(float(gt))
                    if dataset in ['StrategyQA', 'navigate', 'causal_judgement']:
                        gts.append(gt)
                    if dataset == 'web_of_lies':
                        if gt == 'yes':
                            gt = True
                        else:
                            gt = False
                        gts.append(gt)
                    if dataset in ['AQUA', 'logical_deduction_three_objects', 'logical_deduction_five_objects', 'logical_deduction_seven_objects', 'reasoning_about_colored_objects', 'word_sorting', 'tracking_shuffled_objects_three_objects', 'tracking_shuffled_objects_five_objects', 'tracking_shuffled_objects_seven_objects', 'temporal_sequences']:
                        gts.append(gt)    
                    if dataset == 'object_counting':
                        gts.append(float(gt))
    
    return gts