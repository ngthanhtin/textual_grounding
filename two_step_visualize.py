# %%
import pandas as pd

color_map = {
    1: "#FF5733",  # Red
    2: "#33FF57",  # Green
    3: "#3357FF",  # Blue
    4: "#FF33A1",  # Pink
    5: "#FFA533",  # Orange
    6: "#33FFF3",  # Cyan
    7: "#FF5733",  # Coral Red
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
    20: "#FFDD33",  # Golden Yellow
}


# Function to parse formatted phrases from the CSV format
def parse_formatted_phrases(phrases_str):
    phrases = {}
    for line in phrases_str.split("\n"):
        if line.strip() and '[' in line and ']' in line:
            index = int(line.split('[')[-1].split(']')[0].strip())
            phrase = line.split('**')[1].strip()
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
# Read CSV file
# df = pd.read_csv('/Users/tinnguyen/Downloads/LAB_PROJECTS/textual_grounding/results/GSM8K/design_1_2step_grounding/test_2step_grounding_answer_prompt_fs_inst_gemini_20_3rd.csv')
df = pd.read_csv('/Users/tinnguyen/Downloads/LAB_PROJECTS/textual_grounding/results/GSM8K/design_1_2step_grounding_v2/test_2step_grounding_answer_prompt_fs_inst_gemini.csv')

# HTML template for output
html_output = """
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

# Process each row in the CSV
for index, row in df.iterrows():
    original_question = row['question']
    formatted_phrases_str = row['Formatted Phrases']
    answer_text = row['answer']

    # Parse the formatted phrases
    key_phrases = parse_formatted_phrases(formatted_phrases_str)
    
    # Highlight the answer text using specific colors
    highlighted_answer = highlight_text(answer_text, key_phrases, color_map)

    # Add to the HTML output
    html_output += f"""
    <h2>Question:</h2>
    <p>{original_question}</p>
    
    <h3>Key Phrases:</h3>
    <ul>
        {"".join([f'<li><span style="color:{color_map.get(idx, "#000000")};font-weight:bold">{phrase}</span></li>' for idx, phrase in key_phrases.items()])}
    </ul>
    
    <h3>Answer:</h3>
    <p>{highlighted_answer}</p>
    <hr>
    """

# Close the HTML body
html_output += """
</body>
</html>
"""

# %%
# Write the HTML content to a file
with open("questions_answers_highlights.html", "w") as file:
    file.write(html_output)

print("HTML file generated: highlighted_questions_answers.html")

# %%
