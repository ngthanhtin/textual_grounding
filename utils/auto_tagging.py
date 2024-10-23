# gemini
import google.generativeai as genai
from google.generativeai.types import RequestOptions
from google.api_core import retry

from utils.keys import API_KEYS

instruction_for_question = 'Read the question and answer, think about the most important key facts in the question and answer so that the key facts in the answer should be refered back to the key facts in the question. Please extract the shortest and concise key facts that if we remove them it would make it impossible to answer the question. \
Please avoid irrelevant key facts. Provide your detected key facts inside a dictionary (key: value) that the key is key facts in the question and the value is the corresponding key facts in the answer. Please do not paraphrase or change the key facts in the question and answer when generating the dictionary.' # v4

instruction_for_question = 'Read the question and answer. Think about the most important key facts in the question and answer, ensuring that each key fact in the answer is linked back to its corresponding key fact in the question. Each individual numeric value or fact should be tagged separately. Extract the shortest and most concise key facts, and make sure that if any of them were removed, it would make it impossible to answer the question. Do not group multiple facts together; instead, tag each fact separately. Provide your detected key facts inside a dictionary (key1: [value1, value2, etc], key2: [value1, value2, etc], etc) where the key is a key fact in the question, and the value is the corresponding key fact in the answer. Please avoid paraphrasing or changing key facts from the question and answer.' # v5

instruction_for_question = 'Read the question and answer. Detect the exact key facts in both the question and the answer, and map each fact from the question to the corresponding part of the answer without changing, paraphrasing, or introducing new words or phrases to the key facts. Each individual numeric value or fact should be tagged separately. Extract the shortest and most concise key facts, and make sure that if any of them were removed, it would make it impossible to answer the question. Do not tag irrelevant key facts. If two or more facts are consecutive and cannot be meaningfully split, tag them together. Provide your detected key facts inside a dictionary (key1: [value1, value2, etc], key2: [value1, value2, etc], etc) where the key is the exact key fact from the question, and the value is the exact corresponding fact from the answer.' # v6

instruction_for_question = 'Read the question and answer. Detect the exact key facts in both the question and the answer, and map each fact from the question to the corresponding part of the answer without changing, paraphrasing, or introducing new words or phrases to the key facts. If the question just mentions about one object, one character or one location, etc, then you do not need to include that in the fact, whereas, if the question has many objects, characters or locations, etc, please include them in the fact as well. Extract the shortest and most concise key facts, and make sure that if any of them were removed, it would make it impossible to answer the question. Do not tag irrelevant key facts. If two or more facts are consecutive and cannot be meaningfully split, tag them together. Provide your detected key facts inside a dictionary (key1: [value1, value2, etc], key2: [value1, value2, etc], etc) where the key is the exact key fact from the question, and the value is the exact corresponding fact from the answer.' # v7

examples = """
Here are some examples of key facts in some domain that you might find in the question:

Math Problems:
Question: Sam works at the Widget Factory, assembling Widgets. He can assemble 1 widget every 10 minutes. Jack from the loading dock can help assemble widgets when he doesn't have anything else to do. When he helps, they put together 2 complete widgets every 15 minutes. Recently the factory hired Tony to help assemble widgets. Being new to the job, he doesn't work as fast as Sam or Jack. Yesterday Sam worked for 6 hours before he had to leave work early for a dentist appointment. Jack was able to help out for 4 hours before he had to go back to the loading dock to unload a new shipment of widget materials. Tony worked the entire 8-hour shift. At the end of the day, they had completed 68 widgets. How long does it take Tony to assemble a Widget, in minutes?
Key Information:
Sam works at the Widget Factory, assembling Widgets. He can assemble 1 widget every 10 minutes.
Jack from the loading dock can help assemble widgets when he doesn't have anything else to do. When he helps, they put together 2 complete widgets every 15 minutes.
Yesterday Sam worked for 6 hours
Jack was able to help out for 4 hours
Tony worked the entire 8-hour shift.
they had completed 68 widgets.

Question: For every 12 cans you recycle, you receive $0.50, and for every 5 kilograms of newspapers, you receive $1.50. If your family collected 144 cans and 20 kilograms of newspapers, how much money would you receive?
Key Information:
every 12 cans
you receive $0.50
every 5 kilograms of newspapers
you receive $1.50
144 cans
20 kilograms of newspapers

Question: A man is trying to maximize the amount of money he saves each month. In particular, he is trying to decide between two different apartments. The first apartment costs $800 per month in rent and will cost an additional $260 per month in utilities. The second apartment costs $900 per month and will cost an additional $200 per month in utilities. The first apartment is slightly further from the man's work, and the man would have to drive 31 miles per day to get to work. The second apartment is closer, and the man would only have to drive 21 miles to get to work. According to the IRS, each mile a person drives has an average cost of 58 cents. If the man must drive to work 20 days each month, what is the difference between the total monthly costs of these two apartments after factoring in utility and driving-related costs (to the nearest whole dollar)?
Key Information:
The first apartment costs $800 per month in rent and will cost an additional $260 per month in utilities.
The second apartment costs $900 per month and will cost an additional $200 per month in utilities.
The first apartment is slightly further from the man's work, and the man would have to drive 31 miles per day to get to work.
The second apartment is closer, and the man would only have to drive 21 miles to get to work
each mile a person drives has an average cost of 58 cents
drive to work 20 days each month

Question Answering Problems:
Question: At a presentation about post traumatic stress disorder, would Ariana Grande be a topic of relevance?
Key Information:
post traumatic stress disorder
Ariana Grande

Question: Has the Indian Ocean garbage patch not completed two full rotations of debris since its discovery?
Key Information:
Indian Ocean garbage patch
two full rotations of debris

Question: Was the Second Amendment to the United States Constitution written without consideration for black Americans?
Key Information:
Second Amendment to the United States Constitution
black Americans

Logical Reasoning Problems:
Question: The following paragraphs each describe a set of seven objects arranged in a fixed order. The statements are logically consistent within each paragraph. In a golf tournament, there were seven golfers: Ana, Eve, Ada, Dan, Rob, Amy, and Joe. Dan finished third. Ana finished above Ada. Amy finished last. Dan finished below Rob. Eve finished below Ada. Rob finished below Joe. Options: (A) Ana finished third (B) Eve finished third (C) Ada finished third (D) Dan finished third (E) Rob finished third (F) Amy finished third (G) Joe finished third
Key Information:
Dan finished third. 
Ana finished above Ada. 
Amy finished last. 
Dan finished below Rob. 
Eve finished below Ada.
Rob finished below Joe.

Question: The following paragraphs each describe a set of seven objects arranged in a fixed order. The statements are logically consistent within each paragraph. In an antique car show, there are seven vehicles: a bus, a motorcyle, a hatchback, a station wagon, a minivan, a truck, and a limousine. The station wagon is the fourth-newest. The motorcyle is newer than the truck. The station wagon is older than the hatchback. The minivan is newer than the hatchback. The bus is newer than the minivan. The truck is newer than the limousine.
Key Information:
The station wagon is the fourth-newest. 
The motorcycle is newer than the truck. 
The station wagon is older than the hatchback. 
The minivan is newer than the hatchback. 
The bus is newer than the minivan. 
The truck is newer than the limousine.

Question: The following paragraphs each describe a set of seven objects arranged in a fixed order. The statements are logically consistent within each paragraph. On a branch, there are seven birds: a hummingbird, a cardinal, a blue jay, an owl, a raven, a quail, and a robin. The hummingbird is to the left of the quail. The robin is to the left of the cardinal. The blue jay is the leftmost. The cardinal is the fourth from the left. The raven is the third from the right. The owl is the third from the left.
Key Information:
The hummingbird is to the left of the quail. 
The robin is to the left of the cardinal. 
The blue jay is the leftmost.
The cardinal is the fourth from the left. 
The raven is the third from the right. 
The owl is the third from the left.

My Question is:
"""
instruction_for_question = 'Read the question. Detect the exact key facts in the question via following rules:\
1. Do not change, paraphrase, or introduce new words or phrases to the key facts. \
2. If the question just mentions about one object, one character or one location, etc, then you do not need to include that in the fact, whereas, if the question has many objects, characters or locations, etc, please include them in the fact as well. \
3. Extract the shortest and most concise key facts, and make sure that if any of them were removed, it would make it impossible to answer the question. \
4. Do not tag irrelevant key facts. \
5. If two or more facts are consecutive and cannot be meaningfully split, tag them together. \
Provide your detected key facts as the following form:\
    Key Information: ' # v8

# read fs prompt
def read_question_triples(filename):
    # Define data structure to hold triples
    triples = []

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.readlines()
        
        # Temporary storage for each triple
        current_triple = {"Question": "", "Answer": ""}
        current_section = None
        
        for line in content:
            line = line.strip()
            
            if line.startswith("Question:"):
                if current_triple["Question"]:  # Save the previous triple if it exists
                    triples.append(current_triple)
                    current_triple = {"Question": "", "Answer": ""}
                current_section = "Question"
                current_triple["Question"] = line[len("Question:"):].strip()
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
    
def detect_facts_in_question(fewshot_cot_file, instruction=instruction_for_question):
    responses = []
    triple_content = read_question_triples(fewshot_cot_file)
    
    for i, triple in enumerate(triple_content):
        # if i == 2:
        #     break
        # Add color to tags in the question and answer
        question = triple["Question"]
        try:
            genai.configure(api_key=API_KEYS['gemini'])
            model_config = {
                    "temperature": 0,
                    }
            model = genai.GenerativeModel('gemini-1.5-pro-002', 
                                            # generation_config=model_config
                                            )
            # prompt = f"{question}\n{answer}\n{instruction}"
            prompt = f"{examples}\n{question}\n{instruction}"
            response = model.generate_content(prompt, request_options=RequestOptions(retry=retry.Retry(initial=10, multiplier=2, maximum=60, timeout=60)))
            response = response.text

            responses.append(response)
        except:
            print(f"Can not answer the question {i}")
            continue
    return responses

def grounding_facts_to_QA():
    pass

if __name__ == '__main__':
    version = 'v8'
    dataset = 'logical_deduction_seven_objects'
    fewshot_cot_file_path = f'../prompt/{dataset}/fewshot_cot.txt'
    
    responses = detect_facts_in_question(fewshot_cot_file_path)

    # save to txt file
    save_file = f'vis_auto_tagging/{dataset}_fewshot_cot_{version}.txt'
    f = open(save_file, 'w')
    for response in responses:
        f.write(response + '\n')
    f.close()
