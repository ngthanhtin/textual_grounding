# %%
import openai
import anthropic
import pandas as pd
from collections import defaultdict
from utils import extract_parts_1
import re
from keys import API_KEYS

# %%
def extract_tagged_phrases(text):
    # Defaultdict to hold lists of phrases for each tag
    pattern = re.compile(r"<([a-z])>(.*?)<\/[a-z]>")
    
    # Initialize a dictionary where each key is a tag and the value is a list of phrases
    tagged_phrases = defaultdict(list)
    
    # Find all tags and their corresponding phrases
    for tag, phrase in pattern.findall(text):
        tagged_phrases[tag].append(phrase)
    
    return dict(tagged_phrases)

# %%
# Assuming we have an API key for GPT-4o
openai.api_key = 'YOUR_API_KEY'
claude_key = ''

# Function to send a query to GPT-4o for evaluating citation recall
def evaluate_recall_llm(question, statement, tag):
    prompt = f"""
    Evaluate the following Recall:
    
    Tagged Phrases in the Question: {question}
    
    Statement: {statement}
    
    1 - Most information in the statement is supported by or extracted from the tagged phrases in the question. This applies only to cases where the statement and parts of the snippet are almost identical.\n
    0.5 - More than half of the content in the statement is supported by the tagged phrases in the question, but a small portion is either not mentioned or contradicts the tagged phrases in the question. For example, if the statement has two key points and the tagged phrases in the question support only one of them, it should be considered 0.5.\n
    0 - The statement is largely unrelated to the tagged phrases in the question, or most key points in the statement do not align with the content of the tagged phrases in the question.\n
    Ensure that you do not use any information or knowledge outside of the snippet when evaluating.\n
    Please provide the rating. Just return the number.
    """
    # response = openai.Completion.create(
    #     engine="gpt-4o",
    #     prompt=prompt,
    #     max_tokens=10,
    #     temperature=0
    # )
    # return float(response.choices[0].text.strip())
    
    client = anthropic.Anthropic(api_key=API_KEYS['claude'])

    response = client.messages.create(
    model="claude-3-5-sonnet-20240620",
    max_tokens=10,
    temperature=0.0,
    messages=[
    {
    "role": "user",
    "content": f"{prompt}"
    }
    ]
    )

    return float(response.content[0].text.strip())
    

def evaluate_precision_llm(cited_question, answer, tag):
    prompt = f"""
    Evaluate the following Precision:
    
    Tagged Phrases in the Question: {cited_question}
    
    Statement: {answer}
    
    1 - Some key points of the statement are supported by the snippet or extracted from it.\n
    0 - The statement is almost unrelated to the snippet, or all key points of the statement are inconsistent with the snippet content.\n
    Ensure that you do not use any information or knowledge outside of the snippet when evaluating.\n
    Please provide the rating. Just return the number.
    """
    # response = openai.Completion.create(
    #     engine="gpt-4o",
    #     prompt=prompt,
    #     max_tokens=10,
    #     temperature=0
    # )
    
    # return float(response.choices[0].text.strip())

    client = anthropic.Anthropic(api_key=API_KEYS['claude'])

    response = client.messages.create(
    model="claude-3-5-sonnet-20240620",
    max_tokens=10,
    temperature=0.0,
    messages=[
    {
    "role": "user",
    "content": f"{prompt}"
    }
    ]
    )

    return float(response.content[0].text.strip())

# Function to evaluate both citation recall and precision
def evaluate_citation_recall_and_precision(reformatted_question, answer):
    # Extract tagged elements from reformatted question
    question_tags = extract_tagged_phrases(reformatted_question)
    
    # Extract tagged elements from answer
    answer_tags = extract_tagged_phrases(answer)
    
    # Initialize counts for recall and precision
    total_relevant = 0  # Total number of relevant citations (needed citations)
    total_retrieved = 0  # Total number of citations retrieved (actual citations used)
    recall_scores = []  # Store recall scores from GPT-4o
    precision_scores = []  # Store precision scores from GPT-4o
    
    # Recall evaluation: For each question tag, check if it's properly cited in the answer
    for tag, question_phrase in question_tags.items():
        if tag in answer_tags:  # If the tag exists in the answer
            cited_answer_phrases = answer_tags[tag]
            total_relevant += 1
            # Use GPT-4o to evaluate if the tag from the question is used correctly in the answer
            recall_score = evaluate_recall_llm(question_phrase, cited_answer_phrases, tag)
            recall_scores.append(recall_score)
    
    # Precision evaluation: For each answer tag, check if it's relevant to the question
    for tag, answer_phrases in answer_tags.items():
        if tag in question_tags:
            cited_question_phrases = question_tags[tag]
            # for question_phrase in cited_question_phrases:
            total_retrieved += 1
            # Use GPT-4o to evaluate if the answer's citation is relevant to the reformatted question
            precision_score = evaluate_precision_llm(cited_question_phrases, answer_phrases, tag)
            precision_scores.append(precision_score)
    
    # Final recall and precision calculation
    recall = sum(recall_scores) / total_relevant if total_relevant > 0 else 0.0
    precision = sum(precision_scores) / total_retrieved if total_retrieved > 0 else 0.0
    
    return recall, precision

# %%
import pandas as pd
df_path = '/Users/tinnguyen/Downloads/LAB_PROJECTS/textual_grounding/results/GSM8K/design_1_tin_v2/test_grounding_answer_prompt_fs_inst_claude.csv'
df = pd.read_csv(df_path)
questions = df['question'].tolist()
answers = df['answer'].tolist()
# %%
f1s = []
recalls = []
precisions = []
for answer in answers:
    reformatted_question, extracted_answer = extract_parts_1(answer)
    # Run evaluation
    recall, precision = evaluate_citation_recall_and_precision(reformatted_question, answer)
    recalls.append(recall)
    precisions.append(precision)
    f1s.append(2 * (recall * precision) / (recall + precision) if recall + precision > 0 else 0.0)
    
    print(reformatted_question)
    print(f"Citation Recall: {recall}")
    print(f"Citation Precision: {precision}")
    print(f"F1 Score: {f1s[-1]}")

print(f"Average Citation Recall: {sum(recalls) / len(recalls)}")
print(f"Average Citation Precision: {sum(precisions) / len(precisions)}")
print(f"Average F1 Score: {sum(f1s) / len(f1s)}")
# %%
# create a new dataframe to save the results
df = pd.DataFrame(data={'recall': recalls, 'precision': precisions, 'f1_score': f1s})
df.to_csv('test_grounding_answer_prompt_fs_inst_claude_citation_recall_precision_v2_2.csv', index=False)
# %%
