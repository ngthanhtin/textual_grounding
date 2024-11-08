import re

# Function to highlight the tags as you defined before
def highlight_tags(text):
    # Define a color map for different facts
    color_map = {
        1: '#FFD700',  # Gold for <fact1>
        2: '#ADFF2F',  # GreenYellow for <fact2>
        3: '#87CEEB',  # SkyBlue for <fact3>
        4: '#FF69B4',  # HotPink for <fact4>
        5: '#FFA500',  # Orange for <fact5>
        6: '#90EE90',  # LightGreen for <fact6>
        7: '#FF6347',  # Tomato for <fact7>
        8: '#8A2BE2'   # BlueViolet for <fact8>
    }
    
    # Highlight each <fact1> to <fact8> with a corresponding color
    for i in range(1, 9):
        start_tag = f"<fact{i}>"
        end_tag = f"</fact{i}>"
        color = color_map.get(i, '#FFFFFF')  # Default to white if no color is found (though we map up to 8)
        text = text.replace(start_tag, f'<span style="background-color: {color}; font-weight: bold;">')
        text = text.replace(end_tag, '</span>')
    
    return text

# Function to extract examples from the file content
def extract_examples(file_content):
    # Regex to match each full example (Question, Answer Choices, Reformatted Question, Answer)
    # example_pattern = re.compile(r"Question:\s*(.*?)\nAnswer Choices:\s*(.*?)\nReformatted Question:\s*(.*?)\nAnswer:\s*(.*?)\nQuestion:", re.DOTALL)
    example_pattern = re.compile(r"Question:\s*(.*?)\nAnswer Choices:\s*(.*?)\nReformatted Question:\s*(.*?)\nAnswer:\s*(.*?)(?=\nQuestion:|\Z)", re.DOTALL)

    return example_pattern.findall(file_content)

# Function to visualize the examples using HTML
def visualize_examples(examples):
    html_output = "<html><body>"
    for i, (question, answer_choices, reformatted_question, answer) in enumerate(examples):
        # Apply highlighting
        highlighted_question = highlight_tags(question)
        highlighted_answer_choices = highlight_tags(answer_choices.replace("\n", "<br>"))
        highlighted_reformatted_question = highlight_tags(reformatted_question)
        highlighted_answer = highlight_tags(answer.replace("\n", "<br>"))
        
        # Add to HTML output
        html_output += f"<h2>Example {i + 1}</h2>"
        html_output += f"<p><b>Question:</b> {highlighted_question}</p>"
        html_output += f"<p><b>Answer Choices:</b> {highlighted_answer_choices}</p>"
        html_output += f"<p><b>Reformatted Question:</b> {highlighted_reformatted_question}</p>"
        html_output += f"<p><b>Answer:</b> {highlighted_answer}</p>"
    
    html_output += "</body></html>"
    
    # Save the HTML to a file
    with open("reading_visualized_examples.html", "w", encoding="utf-8") as f:
        f.write(html_output)

# Main function to load the file, extract examples, and visualize
def main(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    # Extract the examples
    examples = extract_examples(file_content)
    
    # Visualize the examples
    visualize_examples(examples)

# Example usage: provide the path to your file
file_path = "/Users/tinnguyen/Downloads/LAB_PROJECTS/textual_grounding/prompt/reclor/fewshot_design_1_v4.txt"  # Update with your file path
main(file_path)
