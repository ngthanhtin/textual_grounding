# %%
from utils import index_2_color_map

# Function to parse formatted phrases from the CSV format
def parse_formatted_phrases(phrases_str):
    phrases = {}
    for line in phrases_str.split("\n"):
        if line.strip() and '[' in line and ']' in line:
            index = int(line.split('[')[-1].split(']')[0].strip())
            try:
                phrase = line.split('**')[1].strip()
            except:
                phrase = line
            phrases[index] = phrase
    return phrases

# Function to highlight phrases and their citations in the answer
def highlight_text(text, key_phrases, color_map):
    for index, phrase in key_phrases.items():
        color = color_map.get(index, "#000000")  # Default to black if index has no color
        # Replace the key phrase and corresponding <s> citations with colored HTML span
        if "<s>{" in text:
            print('haha')
            text = text.replace("<s>{"+f"[{index}]", f"<span style='color:{color};font-weight:bold'>")
        else:
            text = text.replace(f"<s>[{index}]", f"<span style='color:{color};font-weight:bold'>")
        text = text.replace(f"</s>", "</span>")
    return text

# %%
def read_question_triples(filename, query_type=1):
    # Define data structure to hold triples
    triples = []

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.readlines()
        
        # Temporary storage for each triple
        current_triple = {"Question": "", "Reformatted Question": "", "Answer": ""}
        current_section = None
        
        for line in content:
            line = line.strip()
            
            if line.startswith("Question:"):
                if current_triple["Question"]:
                    triples.append(current_triple)
                    current_triple = {"Question": "", "Reformatted Question": "", "Answer": ""}
                current_section = "Question"
                current_triple["Question"] = line[len("Question:"):].strip()
            elif line.startswith("Answer:"):
                current_section = "Answer"
                current_triple["Answer"] = line[len("Answer:"):].strip()
            elif line:  # Continue appending to the current section if not empty
                current_section = "Reformatted Question"
                current_triple["Reformatted Question"] += line + "\n"
        # Append the last triple if it's non-empty
        if current_triple["Question"]:
            triples.append(current_triple)
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    return triples

def create_html_content(file_name, save_html_path):
    # HTML template for output
    html_content = """
    <html>
    <head>
        <title>Highlighted Questions and Answers</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
            }}
            .key-phrase {{
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>Highlighted Questions and Answers</h1>
    """
    # Call the function and get the colored content
    triple_content = read_question_triples(file_name)
    # Check if content was processed
    if triple_content:
        for triple in triple_content:
            original_question = triple['Question']
            formatted_phrases_str = triple['Reformatted Question']
            answer_text = triple['Answer']
            # Parse the formatted phrases
            key_phrases = parse_formatted_phrases(formatted_phrases_str)
            
            # Highlight the answer text using specific colors
            highlighted_answer = highlight_text(answer_text, key_phrases, index_2_color_map)

            # Add to the HTML output
            html_content += f"""
            <h2>Question:</h2>
            <p>{original_question}</p>
            
            <h3>Key Phrases:</h3>
            <ul>
                {"".join([f'<li><span style="color:{index_2_color_map.get(idx, "#000000")};font-weight:bold">{phrase}</span></li>' for idx, phrase in key_phrases.items()])}
            </ul>
            
            <h3>Answer:</h3>
            <p>{highlighted_answer}</p>
            <hr>
            """
        
        # Close the HTML tags
        html_content += """
        </body>
        </html>
        """

        # Optionally write to an HTML file
        with open(save_html_path, "w") as file:
            file.write(html_content)

    else:
        print("No content to display.")

file_name = '../prompt/GSM8K/fewshot_grounding_from_key_phrases_v2.txt'
save_html_path = 'fewshot_grounding_from_key_phrases_v2.html'

create_html_content(file_name, save_html_path)
