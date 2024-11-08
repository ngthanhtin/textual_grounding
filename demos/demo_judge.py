# %%
# %%
import openai
import anthropic
import pandas as pd
from collections import defaultdict
from utils.utils import extract_parts_1
import re
from utils.keys import API_KEYS

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

# Function to send a query to GPT-4o for evaluating citation recall
def evaluate_recall_llm(question, statement, tag):
    prompt = f"""
    Evaluate the following Recall:
    
    Tagged Phrases in the Question: {question}
    
    Statement: {statement}
    
    1 - Most information in the statement is supported by or extracted from the tagged phrases in the question. This applies only to cases where the statement and parts of the tagged phrases are almost identical.\n
    0.5 - More than half of the content in the statement is supported by the tagged phrases in the question, but a small portion is either not mentioned or contradicts the tagged phrases in the question. For example, if the statement has two key points and the tagged phrases in the question support only one of them, it should be considered 0.5.\n
    0 - The statement is largely unrelated to the tagged phrases in the question, or most key points in the statement do not align with the content of the tagged phrases in the question.\n
    Ensure that you do not use any information or knowledge outside of the tagged phrases when evaluating.\n
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
    
    1 - Some key points of the statement are supported by the tagged phrases or extracted from it.\n
    0 - The statement is almost unrelated to the tagged phrases, or all key points of the statement are inconsistent with the tagged phrases content.\n
    Ensure that you do not use any information or knowledge outside of the tagged phrases when evaluating.\n
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

# %%
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
llm_model = 'claude'
df_path = f'results/GSM8K/design_1_v3/fs_inst_{llm_model}.csv'
df = pd.read_csv(df_path)
questions = df['question'].tolist()
answers = df['answer'].tolist()

question = "The great dragon, Perg, sat high atop mount Farbo, <a>breathing fire upon anything within a distance of 1000 feet</a>. <b>Polly could throw the gold javelin, the only known weapon that could sleigh the dragon, for a distance of 400 feet</b>, well within the reach of the dragon's flames. But <c>when Polly held the sapphire gemstone, she could throw the javelin three times farther than when not holding the gemstone</c>. If holding the gemstone, how far outside of the reach of the dragon's flames could Polly stand and still hit the dragon with the gold javelin?"
answer = "When Polly holds the sapphire gemstone, she can throw the javelin <c>three times farther</c> than her normal throwing distance of <b>500 feet</b>. This means she can throw the javelin 3 * 400 = 1200 feet while holding the gemstone. The dragon's flames reach <a>a distance of 900 feet</a>. To find out how far outside the dragon's flame reach Polly can stand, we need to subtract the dragon's flame reach from Polly's throwing distance with the gemstone: 1200 feet (Polly's throw with gemstone) - <a>1000 feet</a> (dragon's flame reach) = 200 feet. Therefore, Polly can stand 200 feet outside the reach of the dragon's flames and still hit the dragon with the gold javelin when holding the sapphire gemstone. The answer is 200."

# %%

recall, precision = evaluate_citation_recall_and_precision(question, answer)
print(recall, precision)