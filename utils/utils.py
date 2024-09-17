import re, json

def read_jsonl_file(filepath):
    data = [] 
    with open(filepath, 'r') as file:
        for line in file:
            json_obj = json.loads(line)  # Parse the JSON data from the line
            data.append(json_obj)  # Add the parsed JSON object to a list
    return data

# Function to replace tags with colored tags
def add_color_to_tags(text):
    # tag_color_mapping = {
    #     'a': 'yellow',  
    #     'b': 'lightblue',
    #     'c': 'lightgreen',
    #     'd': 'lightcoral',
    #     'e': 'lightcyan', 
    #     'f': 'orange',
    # }
    tag_color_mapping = {
        'fact_1': 'yellow',  
        'fact_2': 'lightblue',
        'fact_3': 'lightgreen',
        'fact_4': 'lightcoral',
        'fact_5': 'lightcyan', 
        'fact_6': 'orange',
    }
    # Iterate over the tag-color mappings
    for tag, color in tag_color_mapping.items():
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
    original_tags = re.findall(r'<([abcde])>(.*?)<\/\1>', original_text)
    reformulated_tags = re.findall(r'<([abcde])>(.*?)<\/\1>', reformulated_text)

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
    return sum(ious) / len(ious) if ious else 0, len(original_tags), len(reformulated_tags)

# Function to extract parts of the text based on a heading pattern
def extract_parts_0(text):
    # Find the Reformatted Question and Answer using regex
    question_match = re.search(r"Reformatted Question:\n(.*?)(?=\n[A-Z])", text, re.S)
    answer_match = re.search(r"Answer:\n(.*)", text, re.S)

    # Extracting text for each part
    question_text = question_match.group(1).strip() if question_match else "Question not found"
    answer_text = answer_match.group(1).strip() if answer_match else "Answer not found"

    return question_text, answer_text

# Function to extract parts of the text based on headers
def extract_parts_1(text):
    # Find the "Reformatted Question" and "Answer" sections
    # question_match = re.search(r"Reformatted Question:(.*?)\nAnswer:", text, re.S)
    # answer_match = re.search(r"Answer:(.*)", text, re.S)
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