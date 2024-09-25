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

def markdown_to_html_highlight(text):
    """
    Converts markdown bold (**text**) to HTML with highlighted spans.
    """
    
    text = text.replace('<ref>', '(<ref style="color: green;">')
    text = text.replace('</ref>', '</ref>)')
    
    text = text.replace('<a>', '(<a class="highlight">')
    
    # Regex to find **text**
    pattern = r'\*\*(.*?)\*\*'
    # Replace **text** with <span class="highlight">text</span>
    # text = re.sub(pattern, r'<span class="highlight">\1</span>', text)
    
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

def extract_parts_only_answer(text):
    # Regex pattern to match variations of "Reformatted Question" and "Answer" headers
    pattern = r"(?:\*\*|##)?\s*(Answer)\s*[:\*\*]*\s*(.*?)(?=(?:\*\*|##)?\s*(Reformatted Question|Answer|$))"

    results = []
    
    found = re.findall(pattern, text, re.S | re.I)
    if found:
        results.append({key.strip(): value.strip() for key, value, _ in found})
        return results[0]['Answer']
    else:
        return "Answer not found"
    
# def extract_parts(text):
#     # Regex pattern to match variations of "Reformatted Question" and "Answer" headers
#     pattern = r"(?:\*\*|##)?\s*(Reformatted Question|Answer)\s*[:\*\*]*\s*(.*?)(?=(?:\*\*|##)?\s*(Reformatted Question|Answer|$))"

#     results = []
    
#     found = re.findall(pattern, text, re.S | re.I)
#     if found:
#         results.append({key.strip(): value.strip() for key, value, _ in found})
#         return results[0]['Reformatted Question'], results[0]['Answer']
#     else:
#         return "Question not found", "Answer not found"
    
def extract_conclusion(text, prefix="The answer is"):
    pattern = rf"{re.escape(prefix)}\s*(\d+|\w+)[^\n]*"
    match = re.search(pattern, text)
    return match.group(0) if match else "No clear answer found"

def extract_number(text):
    # Regex to find numeric patterns, including those with commas
    match = re.search(r"\$?(\d{1,9}(?:,\d{3})*(?:\.\d+)?)", text)
    return match.group(1) if match else "No number found"

def count_tags(text):
    # Find all the tags using a regular expression
    tags = re.findall(r'<([a-z])>', text)
    
    # Count the occurrences of each tag using Counter
    tag_counts = Counter(tags)
    
    return tag_counts

def check_for_word(text, option):
    # Validate the option to make sure it's either "yes" or "no"
    # if option.lower() not in ["yes", "no"]:
    #     return False

    # Pattern to find the specified word using regular expressions
    pattern = rf'\b{re.escape(option)}\b'
    
    # Use re.search to check if the specified word is in the text as a whole word
    match = re.search(pattern, text, re.IGNORECASE)  # re.IGNORECASE makes the search case-insensitive
    
    # Return True if a match is found, otherwise False
    return bool(match)

def extract_last_sentence(text):
    # Split the text into sentences using regular expression to handle punctuation.
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    
    # Return the last sentence after stripping any extra spaces.
    return sentences[-1].strip() if sentences else text