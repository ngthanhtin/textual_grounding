import re, os
from utils import add_color_to_tags

def read_question_doubles(filename):
    # Define data structure to hold triples
    doubles = []

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.readlines()
        
        # Temporary storage for each triple
        current_double = {"Tagged Question": "", "Tagged Answer": ""}
        current_section = None
        
        for line in content:
            line = line.strip()
            
            if line.startswith("Tagged Question:"):
                if current_double["Tagged Question"]:  # Save the previous triple if it exists
                    doubles.append(current_double)
                    current_double = {"Question": "", "Answer": ""}
                current_section = "Tagged Question"
                current_double["Tagged Question"] = line[len("Tagged Question:"):].strip()
            elif line.startswith("Tagged Answer:"):
                current_section = "Tagged Answer"
                current_double["Tagged Answer"] = line[len("Tagged Answer:"):].strip()
            elif line:  # Continue appending to the current section if not empty
                current_double[current_section] += " " + line
        
        # Append the last triple if it's non-empty
        if current_double["Tagged Question"]:
            doubles.append(current_double)
        
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    return doubles

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
 
def create_html_content(file_name, save_html_path, extracted_objects=None, grounding_facts=None):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Auto Tagging</title>
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
    # triple_content = read_question_triples(file_name)
    
    triple_content = extracted_objects
    # Check if content was processed
    if triple_content:
        if grounding_facts: # visualize ground step
            # for i, (triple, extracted_object, double) in enumerate(zip(triple_content, extracted_objects, grounding_facts)):    
            for i, (extracted_object, double) in enumerate(zip(extracted_objects, grounding_facts)):
                # Add color to tags in the question and answer
                # question = add_color_to_tags(triple["Reformatted Question"])
                # answer = add_color_to_tags(triple["Answer"])
                
                html_content += f"<div class='container'>"
                # html_content += f"<div class='question'><strong>Reformatted Question:</strong> {question}<br><strong>Answer:</strong>{answer}</div>"
                # html_content += f"<div class='question'><strong>Reformatted Question:</strong> {question}<br><strong>Answer:</strong>{answer}</div>"
                
                # if the obj in the question add tag <factn> to that specific question
                # question = triple["Question"]
                
                # tagged_question = double["Tagged Question"]
                # tagged_answer = double["Tagged Answer"]
                tagged_answer = double
                # Add color to tags in the question and answer
                tagged_question = add_color_to_tags(extracted_object)
                tagged_answer = add_color_to_tags(tagged_answer)
                
                # for k, obj in enumerate(extracted_object):
                #     if obj in question:
                #         question = question.replace(obj, f"<fact{k+1}>{obj}</fact{k+1}>")
                # extracted_object = [f"<fact{k+1}>{obj}</fact{k+1}>" for k, obj in enumerate(extracted_object)]
                # extracted_object = ' '.join(extracted_object)
                
                # question = add_color_to_tags(question)
                answer = add_color_to_tags(extracted_object)
                html_content += f"<div class='question'><strong>{i}/ Tagged Question:</strong>{tagged_question}<br><br><strong>Tagged Answer:</strong>{tagged_answer}</div>"
                
                html_content += "</div>\n"
            
            # Close the HTML tags
            html_content += """
            </body>
            </html>
            """
        else: # visualize detect step
            for i, (triple, extracted_object) in enumerate(zip(triple_content, extracted_objects)):
                # Add color to tags in the question and answer
                tagged_question = add_color_to_tags(extracted_object)
                
                html_content += f"<div class='container'>"
                html_content += f"<div class='question'><strong>Tagged Question:</strong>{tagged_question}</div>"
                
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
dataset = 'reasoning_about_colored_objects'
datasets = ['AQUA', 'ASDiv', 'GSM8K', 'SVAMP', 'MultiArith',  'StrategyQA', 'wikimultihopQA', 'causal_judgement', 'coin', 'date', 'reclor', 'navigate', 'logical_deduction_seven_objects', 'reasoning_about_colored_objects']
# datasets = ['AQUA', 'ASDiv', 'GSM8K', 'SVAMP', 'MultiArith']
datasets = ['commonsenseQA']

for dataset in datasets:
    version = 'v13'
    fewshot_file_name = f'../prompt/{dataset}/fewshot_design_1_v4.txt'
    step = 'ground'
    detected_key_fact_cot = f"vis_auto_tagging/detect/{dataset}_detect_{version}.txt"
    grounding_facts = f'vis_auto_tagging/ground_v13/{dataset}_ground_{version}.txt'

    with open(detected_key_fact_cot, 'r') as file:
        file_content = file.readlines()
    file_content = [line.strip() for line in file_content if line != '\n']
    extracted_keyfacts = file_content

    # Using regex to extract each "Key Information" block
    with open(grounding_facts, 'r') as file:
        file_content = file.read()
    pattern = r'### TAGGED ANSWER:(.*?)(?=(\n### TAGGED ANSWER:|\Z))'
    file_content = re.findall(pattern, file_content, re.DOTALL)
    file_content = [block[0].strip() for block in file_content]
    ####


    if step == 'detect':
        save_html_path = f'vis_auto_tagging/detect/{dataset}_detect_{version}.html'
        create_html_content(fewshot_file_name, save_html_path, extracted_keyfacts, grounding_facts=None)
        
    elif step == 'ground':
        save_html_path = f'vis_auto_tagging/ground_v13/{dataset}_ground_v13.html'
        # grounding_facts = read_question_doubles(grounding_facts)
        grounding_facts
        with open(grounding_facts, 'r') as file:
            file_content = file.readlines()
        
        grounding_facts = [line.strip() for line in file_content if line not in ['### TAGGED ANSWER:', '\n']]
        
        
        grounding_facts = [line for line in grounding_facts if line != '### TAGGED ANSWER:']
        
        # grounding_facts = re.findall(r'TAGGED ANSWER:\n(.*?)(?=\n\n|$)', file_content, re.DOTALL)
        
        create_html_content(fewshot_file_name, save_html_path, extracted_keyfacts, grounding_facts)
        
        save_file = f'../prompt_auto_tagging/{dataset}/fewshot_design_1_v4.txt'
        os.makedirs(os.path.dirname(save_file), exist_ok=True)
        for i, (extracted_object, double) in enumerate(zip(extracted_keyfacts, grounding_facts)):
                tagged_question = extracted_object
                tagged_answer = double
                
                # save to text file                
                # f = open(save_file, 'a')
                # f.write(f"Question: {tagged_question}\nAnswer: {tagged_answer}\n\n")
                # f.close()
        
        
