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
            json_obj = json.loads(line)
            data.append(json_obj)
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