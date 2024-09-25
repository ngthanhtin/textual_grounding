from utils import add_color_to_tags

def read_question_triples(filename):
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
                if current_triple["Question"]:  # Save the previous triple if it exists
                    triples.append(current_triple)
                    current_triple = {"Question": "", "Reformatted Question": "", "Answer": ""}
                current_section = "Question"
                current_triple["Question"] = line[len("Question:"):].strip()
            elif line.startswith("Reformatted Question:"):
                current_section = "Reformatted Question"
                current_triple["Reformatted Question"] = line[len("Reformatted Question:"):].strip()
            elif line.startswith("Answer:"):
                current_section = "Answer"
                current_triple["Answer"] = line[len("Answer:"):].strip()
            elif line:  # Continue appending to the current section if not empty
                current_triple[current_section] += " " + line
        
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
 
def create_html_content(filename, save_html_path):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Question and Answer Highlights</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            .highlight {
                background-color: #FFFF00; /* Yellow background for visibility */
                font-weight: bold; /* Bold text for emphasis */
            }
            .container {
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }
            .question, .answer {
                flex: 1;
                padding: 10px;
            }
        </style>
    </head>
    <body>
    """
    # Call the function and get the colored content
    triple_content = read_question_triples(file_name)

    # Check if content was processed
    if triple_content:
        for triple in triple_content:
            # Add color to tags in the question and answer
            question = add_color_to_tags(triple["Reformatted Question"])
            answer = add_color_to_tags(triple["Answer"])
            
            html_content += f"<div class='container'>"
            html_content += f"<div class='question'><strong>Reformatted Question:</strong> {question}</div>"
            html_content += f"<div class='answer'><strong>Answer:</strong>{answer}</div>"
            html_content += "</div>\n"
        
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


# Specify the file name
file_name = '../prompt/GSM8K/fewshot_design_1_v4.txt'
save_html_path = 'vis_fs/fewshot_design_1_v4.html'

create_html_content(file_name, save_html_path)