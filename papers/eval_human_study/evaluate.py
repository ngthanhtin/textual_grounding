# %%
import pandas as pd
import json, os

path = 'session_data/'

files = os.listdir(path)

dict_ = {'tagged': {'num_correct_label': 0, 'num_incorrect_label': 0, 'false_negative': {'num': 0, 'time': 0}, 'false_positive': {'num': 0, 'time': 0}, 'true_positive': {'num': 0, 'time': 0}, 'true_negative': {'num': 0, 'time': 0}}, 'non_tagged': {'num_correct_label': 0, 'num_incorrect_label': 0, 'false_negative': {'num': 0, 'time': 0}, 'false_positive': {'num': 0, 'time': 0}, 'true_positive': {'num': 0, 'time': 0}, 'true_negative': {'num': 0, 'time': 0}}}


# Initialize session count
num_sessions = 0
num_tag_sessions = 0
num_non_tag_sessions = 0

for file in files:
    if 'admin' in file:
        continue
    
    if 'giang' in file.lower():
        continue
    
    if 'pooyan' in file.lower():
        continue
    
    if 'logantest' in file.lower():
        continue
    
    num_sessions += 1
    
    file_path = os.path.join(path, file)


    # Load Data by json
    data = json.load(open(file_path))
    isTagged = data['isTagged']
    questions = data['questions']
    responses = data['responses']
    
    if isTagged:
        num_tag_sessions += 1
    else:
        num_non_tag_sessions += 1
    
    
    # Iterate through questions and responses
    for response, question in zip(responses, questions):
        binary_gt = question['isTrue']  # Ground truth: 1 (True), 0 (False)
        binary_pred = 1 if response['user_choice'] == "Correct" else 0  # Predicted: 1 (Correct), 0 (Incorrect)
        time_spent = response.get('time_spent_seconds', 0)  # Get time spent, default to 0
        
        # Select the correct dictionary based on tagging
        tag_type = 'tagged' if isTagged == 1 else 'non_tagged'
        
        if binary_gt == 1:
            dict_[tag_type]['num_correct_label'] += 1
        else:
            dict_[tag_type]['num_incorrect_label'] += 1
            
        # Classify the result
        if binary_gt == 1 and binary_pred == 1:
            dict_[tag_type]['true_positive']['num'] += 1
            dict_[tag_type]['true_positive']['time'] += time_spent
        elif binary_gt == 0 and binary_pred == 1:
            dict_[tag_type]['false_positive']['num'] += 1
            dict_[tag_type]['false_positive']['time'] += time_spent
        elif binary_gt == 1 and binary_pred == 0:
            dict_[tag_type]['false_negative']['num'] += 1
            dict_[tag_type]['false_negative']['time'] += time_spent
        elif binary_gt == 0 and binary_pred == 0:
            dict_[tag_type]['true_negative']['num'] += 1
            dict_[tag_type]['true_negative']['time'] += time_spent

# %%
print("Number of sessions: ", num_sessions)
print("Number of tagged sessions: ", num_tag_sessions)
print("Number of non-tagged sessions: ", num_non_tag_sessions)
# %%
print(dict_)
# compute average time per question for tagged and nontagged questions
total_time_tagged_questions = dict_['tagged']['true_positive']['time'] + dict_['tagged']['false_negative']['time'] + dict_['tagged']['false_positive']['time'] + dict_['tagged']['true_negative']['time']

total_questions = dict_['tagged']['num_correct_label'] + dict_['tagged']['num_incorrect_label']
print("Tagged Average Time: ", total_time_tagged_questions/total_questions)
# %%
total_time_non_tagged_questions = dict_['non_tagged']['true_positive']['time'] + dict_['non_tagged']['false_negative']['time'] + dict_['non_tagged']['false_positive']['time'] + dict_['non_tagged']['true_negative']['time']
total_questions = dict_['non_tagged']['num_correct_label'] + dict_['non_tagged']['num_incorrect_label']
print("Non-Tagged Average Time: ", total_time_non_tagged_questions/total_questions)
# %%
# Function to compute accuracy for cases that have LLM answer is correct (TP)
def compute_correct_metrics(data):
    correct_time = data['true_positive']['time'] + data['false_negative']['time']
    correct_count = data['true_positive']['num']
    
    total_correct_cases = data['num_correct_label']
    accuracy = (correct_count / total_correct_cases) * 100 if total_correct_cases > 0 else 0
    avg_time = correct_time / correct_count if correct_count > 0 else 0
    return accuracy, avg_time

# %%
# Function to compute accuracy for cases that have LLM answer is wrong (TN)
def compute_wrong_metrics(data):
    wrong_time = data['false_positive']['time'] + data['true_negative']['time']
    wrong_count = data['true_negative']['num']
    
    total_incorrect_cases = data['num_incorrect_label']
    error_rate = (wrong_count / total_incorrect_cases) * 100 if total_incorrect_cases > 0 else 0
    avg_time = wrong_time / wrong_count if wrong_count > 0 else 0
    return error_rate, avg_time

# Metrics for tagged data
tagged_correct_accuracy, tagged_correct_time = compute_correct_metrics(dict_['tagged'])
tagged_wrong_accuracy, tagged_wrong_time = compute_wrong_metrics(dict_['tagged'])

# Metrics for non-tagged data
non_tagged_correct_accuracy, non_tagged_correct_time = compute_correct_metrics(dict_['non_tagged'])
non_tagged_wrong_accuracy, non_tagged_wrong_time = compute_wrong_metrics(dict_['non_tagged'])


print("Tagged Correct Accuracy: ", tagged_correct_accuracy)
print("Tagged Correct Time: ", tagged_correct_time)
print("Non-Tagged Correct Accuracy: ", non_tagged_correct_accuracy)
print("Non-Tagged Correct Time: ", non_tagged_correct_time)

print("Tagged Wrong Accuracy: ", tagged_wrong_accuracy)
print("Tagged Wrong Time: ", tagged_wrong_time)
print("Non-Tagged Wrong Accuracy: ", non_tagged_wrong_accuracy)
print("Non-Tagged Wrong Time: ", non_tagged_wrong_time)
# %%
# Function to compute total accuracy
def compute_accuracy(correct_predict_count, total_cases):
    return (correct_predict_count / total_cases) * 100

# Compute correct and wrong counts for tagged and non-tagged
tagged_correct_predict_count = dict_['tagged']['true_positive']['num'] + dict_['tagged']['true_negative']['num']

non_tagged_correct_predict_count = dict_['non_tagged']['true_positive']['num'] + dict_['non_tagged']['true_negative']['num']

total_tagged_cases = dict_['tagged']['num_correct_label'] + dict_['tagged']['num_incorrect_label']
total_non_tagged_cases = dict_['non_tagged']['num_correct_label'] + dict_['non_tagged']['num_incorrect_label']

tagged_accuracy = compute_accuracy(tagged_correct_predict_count, total_tagged_cases)
non_tagged_accuracy = compute_accuracy(non_tagged_correct_predict_count, total_non_tagged_cases)

print("Tagged Accuracy: ", tagged_accuracy)
print("Non-Tagged Accuracy: ", non_tagged_accuracy)
# %%
