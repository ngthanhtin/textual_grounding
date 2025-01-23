# %%
import pandas as pd
import json, os
from datetime import datetime

def quarter_percentile(files):
    filtered_files = []
    for file in files:
        if 'admin' in file:
            continue
        
        if 'giang' in file.lower():
            continue
        
        if 'pooyan' in file.lower():
            continue
        
        if 'logantest' in file.lower():
            continue
        
        if 'mehrshad' in file.lower():
            continue
        
        filtered_files.append(file)
    
    all_accs = {"tagged": [], "non_tagged": []}
    for file in filtered_files:
        file_path = os.path.join(path, file)

        # Load Data by json
        data = json.load(open(file_path))
        start_time = data['start_time']
        isTagged = data['isTagged']
        questions = data['questions']
        responses = data['responses']
        practice_result = data['practice_result']
        
        if practice_result != 'correct':
            continue
        
        acc = 0
        answerable_questions = 0
        tag_type = 'tagged' if isTagged == 1 else 'non_tagged'
        
        for response, question in zip(responses, questions):
            if 'timed_out' not in response.keys() or 'time_spent_seconds' not in response.keys():
                continue
            
            binary_gt = question['isTrue']  # Ground truth: 1 (True), 0 (False)
            binary_pred = 1 if response['user_choice'] == "Correct" else 0  # 
            
            if binary_gt == binary_pred:
                acc += 1
            
            answerable_questions += 1
        
        if answerable_questions == 0:
            continue
        all_accs[tag_type].append(acc/answerable_questions)
        
    all_accs['tagged'].sort()
    all_accs['non_tagged'].sort()
    # remove 25% percentile
    filtered_accs = {'tagged': [], 'non_tagged': []}
    mean_accs = {'tagged': 0, 'non_tagged': 0}
    std_accs = {'tagged': 0, 'non_tagged': 0}
    for key in all_accs:
        accs = all_accs[key]
        filtered_accs[key] = accs[:int(0.25*len(accs))]
    # compute mean accuracy
    mean_accs = {key: sum(filtered_accs[key]) / len(filtered_accs[key]) for key in filtered_accs}
    # compute std accuracy
    std_accs = {key: (sum([(x - mean_accs[key]) ** 2 for x in filtered_accs[key]]) / len(filtered_accs[key])) ** 0.5 for key in filtered_accs}

    return mean_accs, std_accs

# Function to compute accuracy for cases that have LLM answer is wrong (TN)
def compute_wrong_metrics(data):
    wrong_time = data['false_positive']['time']
    wrong_count = data['true_negative']['num']
    
    total_incorrect_cases = data['num_incorrect_label']
    error_rate = (wrong_count / total_incorrect_cases) * 100
    avg_time = wrong_time / total_incorrect_cases
    return error_rate, avg_time

# Function to compute accuracy for cases that have LLM answer is correct (TP)
def compute_correct_metrics(data):
    correct_time = data['true_positive']['time']
    correct_count = data['true_positive']['num']
    
    total_correct_cases = data['num_correct_label']
    accuracy = (correct_count / total_correct_cases) * 100
    avg_time = correct_time / total_correct_cases
    return accuracy, avg_time

path = 'grounding_human_preference_data/session_data/'

files = os.listdir(path)

dict_ = {'tagged': {'num_correct_label': 0, 'num_incorrect_label': 0, 'false_negative': {'num': 0, 'time': 0}, 'false_positive': {'num': 0, 'time': 0}, 'true_positive': {'num': 0, 'time': 0}, 'true_negative': {'num': 0, 'time': 0}}, 'non_tagged': {'num_correct_label': 0, 'num_incorrect_label': 0, 'false_negative': {'num': 0, 'time': 0}, 'false_positive': {'num': 0, 'time': 0}, 'true_positive': {'num': 0, 'time': 0}, 'true_negative': {'num': 0, 'time': 0}}}

accs = {"tagged": [], "non_tagged": []}
times = {"tagged": [], "non_tagged": []}
# Initialize session count
time_answer_threshold = 0

num_sessions = 0
num_tag_sessions = 0
num_non_tag_sessions = 0
num_time_out = 0
num_below_threshold = 0
num_tag_below_threshold = 0
num_non_tag_below_threshold = 0

num_practice_result_incorrect = 0

# %%
# remove 25% percentile
mean_acc, std_acc = quarter_percentile(files)
print("Mean Accuracy: ", mean_acc)
print("Std Accuracy: ", std_acc)

# %%    
total_responses = {'tagged': 0, 'non_tagged': 0}
for file in files:
    if 'admin' in file.lower():
        continue
    
    if 'giang' in file.lower():
        continue
    
    if 'pooyan' in file.lower():
        continue
    
    if 'logantest' in file.lower():
        continue
    
    if 'mehrshad' in file.lower():
        continue
    
    if 'pp' in file.lower():
        continue
    
    if 'test' in file.lower():
        continue
    
    num_sessions += 1
    
    file_path = os.path.join(path, file)


    # Load Data by json
    data = json.load(open(file_path))
    start_time = data['start_time']
    isTagged = data['isTagged']
    questions = data['questions']
    responses = data['responses']
    practice_result = data['practice_correct']
    
    # Parse the start time into a datetime object
    start_datetime = datetime.fromisoformat(start_time)
    cutoff_date = datetime(2025, 1, 15)
    if start_datetime < cutoff_date:
        continue
    
    if practice_result < 2:
        num_practice_result_incorrect += 1
        continue
    
    if isTagged:
        num_tag_sessions += 1
    else:
        num_non_tag_sessions += 1
    
    # Select the correct dictionary based on tagging
    tag_type = 'tagged' if isTagged == 1 else 'non_tagged'
    
    # Iterate through questions and responses
    temp_acc = 0
    temp_time = 0
    temp_len_response = 0
    for response, question in zip(responses, questions):
        if response['timed_out'] == True and response['user_choice'] == None:
            # print(response)
            # print('-----')
            continue
        
        if response['timed_out'] == True:
            time_spent = 120
            num_time_out += 1
        else:
            time_spent = response.get('time_spent_seconds', 0)  # Get time spent, default to 0

        # if response['time_spent_seconds'] < time_answer_threshold:
        #     num_below_threshold += 1
            if isTagged:
                num_tag_below_threshold += 1
            else:
                num_non_tag_below_threshold += 1
            # continue
        
        binary_gt = question['isTrue']  # Ground truth: 1 (True), 0 (False)
        binary_pred = 1 if response['user_choice'] == "Correct" else 0  # Predicted: 1 (Correct), 0 (Incorrect)
        
        
        if binary_gt == 1:
            dict_[tag_type]['num_correct_label'] += 1
        else:
            dict_[tag_type]['num_incorrect_label'] += 1
            
        # Classify the result
        temp_len_response += 1
        if binary_gt == 1 and binary_pred == 1:
            dict_[tag_type]['true_positive']['num'] += 1
            dict_[tag_type]['true_positive']['time'] += time_spent
            temp_acc += 1
            temp_time += time_spent
        elif binary_gt == 0 and binary_pred == 1:
            dict_[tag_type]['false_positive']['num'] += 1
            dict_[tag_type]['false_positive']['time'] += time_spent
        elif binary_gt == 1 and binary_pred == 0:
            dict_[tag_type]['false_negative']['num'] += 1
            dict_[tag_type]['false_negative']['time'] += time_spent
        elif binary_gt == 0 and binary_pred == 0:
            dict_[tag_type]['true_negative']['num'] += 1
            dict_[tag_type]['true_negative']['time'] += time_spent
            temp_acc += 1
            temp_time += time_spent
    
    total_responses[tag_type] += temp_len_response       
    
    
    accs[tag_type].append(temp_acc/temp_len_response)
    times[tag_type].append(temp_time/temp_len_response)

# %%
print(sum(accs['tagged']), sum(accs['non_tagged']))
print(total_responses)
# %% compute mean and std
def compute_mean_std(list_):
    mean = sum(list_) / len(list_)
    std = (sum([(x - mean) ** 2 for x in list_]) / len(list_)) ** 0.5
    return mean, std

mean_acc_tagged, std_acc_tagged = compute_mean_std(accs['tagged'])
mean_acc_non_tagged, std_acc_non_tagged = compute_mean_std(accs['non_tagged'])

mean_time_tagged, std_time_tagged = compute_mean_std(times['tagged'])
mean_time_non_tagged, std_time_non_tagged = compute_mean_std(times['non_tagged'])

print("=== Summary ===")
print("Mean Accuracy Tagged: ", mean_acc_tagged)
print("Std Accuracy Tagged: ", std_acc_tagged)
print("Mean Time Tagged: ", mean_time_tagged)
print("Std Time Tagged: ", std_time_tagged)

print("Mean Accuracy Non-Tagged: ", mean_acc_non_tagged)
print("Std Accuracy Non-Tagged: ", std_acc_non_tagged)
print("Mean Time Non-Tagged: ", mean_time_non_tagged)
print("Std Time Non-Tagged: ", std_time_non_tagged)

print("Time Answer Threshold: ", time_answer_threshold)
print("Number of practice results incorrect: ", num_practice_result_incorrect)
print("Number of sessions: ", num_sessions)
print("Number of tagged sessions: ", num_tag_sessions)
print("Number of non-tagged sessions: ", num_non_tag_sessions)
# print("Number of time out sessions: ", num_time_out)
# print("Number of below threshold sessions: ", num_below_threshold)
# print("Number of tagged below threshold sessions: ", num_tag_below_threshold)
# print("Number of non-tagged below threshold sessions: ", num_non_tag_below_threshold)


# %% -- Compute Sensitivity and Specificity----
# print TP, TN, FP, FN
print("=== Tagged Data ===")
print("True Positive: ", dict_['tagged']['true_positive']['num'])
print("True Negative: ", dict_['tagged']['true_negative']['num'])
print("False Positive: ", dict_['tagged']['false_positive']['num'])
print("False Negative: ", dict_['tagged']['false_negative']['num'])
print("=== Non-Tagged Data ===")
print("True Positive: ", dict_['non_tagged']['true_positive']['num'])
print("True Negative: ", dict_['non_tagged']['true_negative']['num'])
print("False Positive: ", dict_['non_tagged']['false_positive']['num'])
print("False Negative: ", dict_['non_tagged']['false_negative']['num'])


# compute average time per question for tagged and nontagged questions
total_time_tagged_questions = dict_['tagged']['true_positive']['time'] + dict_['tagged']['false_negative']['time'] + dict_['tagged']['false_positive']['time'] + dict_['tagged']['true_negative']['time']

# total_questions = dict_['tagged']['num_correct_label'] + dict_['tagged']['num_incorrect_label']
# print("Tagged Average Time: ", total_time_tagged_questions/total_questions)

total_time_non_tagged_questions = dict_['non_tagged']['true_positive']['time'] + dict_['non_tagged']['false_negative']['time'] + dict_['non_tagged']['false_positive']['time'] + dict_['non_tagged']['true_negative']['time']
# total_questions = dict_['non_tagged']['num_correct_label'] + dict_['non_tagged']['num_incorrect_label']
# print("Non-Tagged Average Time: ", total_time_non_tagged_questions/total_questions)

# Metrics for tagged data
tagged_correct_accuracy, tagged_correct_time = compute_correct_metrics(dict_['tagged'])
tagged_wrong_accuracy, tagged_wrong_time = compute_wrong_metrics(dict_['tagged'])

# Metrics for non-tagged data
non_tagged_correct_accuracy, non_tagged_correct_time = compute_correct_metrics(dict_['non_tagged'])
non_tagged_wrong_accuracy, non_tagged_wrong_time = compute_wrong_metrics(dict_['non_tagged'])


print("=== Tagged Data ===")
print("Tagged Correct Accuracy: ", tagged_correct_accuracy)
print("Tagged Correct Time: ", tagged_correct_time)
print("Tagged Wrong Accuracy: ", tagged_wrong_accuracy)
print("Tagged Wrong Time: ", tagged_wrong_time)
print("=== Non-Tagged Data ===")
print("Non-Tagged Correct Accuracy: ", non_tagged_correct_accuracy)
print("Non-Tagged Correct Time: ", non_tagged_correct_time)
print("Non-Tagged Wrong Accuracy: ", non_tagged_wrong_accuracy)
print("Non-Tagged Wrong Time: ", non_tagged_wrong_time)

# %%
# # Function to compute total accuracy
# def compute_accuracy(correct_predict_count, total_cases):
#     return (correct_predict_count / total_cases) * 100

# # Compute accuracy for tagged and non-tagged
# tagged_correct_predict_count = dict_['tagged']['true_positive']['num'] + dict_['tagged']['true_negative']['num']
# print(tagged_correct_predict_count)

# non_tagged_correct_predict_count = dict_['non_tagged']['true_positive']['num'] + dict_['non_tagged']['true_negative']['num']
# print(non_tagged_correct_predict_count)
# total_tagged_cases = dict_['tagged']['num_correct_label'] + dict_['tagged']['num_incorrect_label']
# print(total_tagged_cases)
# total_non_tagged_cases = dict_['non_tagged']['num_correct_label'] + dict_['non_tagged']['num_incorrect_label']
# print(total_non_tagged_cases)
# tagged_accuracy = compute_accuracy(tagged_correct_predict_count, total_tagged_cases)
# non_tagged_accuracy = compute_accuracy(non_tagged_correct_predict_count, total_non_tagged_cases)

# print("Tagged Accuracy: ", tagged_accuracy)
# print("Non-Tagged Accuracy: ", non_tagged_accuracy)

# %%
import matplotlib.pyplot as plt

# Data from the user
data = {
    "Mean Accuracy": [67.9, 71.55],
    "Std Accuracy": [22.04, 19.07],
    "Mean Time": [30.62, 43.65],
    "Std Time": [18.02, 17.84]
}

categories = ['Tagged', 'Non-Tagged']

# Creating the bar chart
fig, ax = plt.subplots(2, 1, figsize=(10, 8))

# Plotting Accuracy
ax[0].bar(categories, data['Mean Accuracy'], yerr=data['Std Accuracy'], capsize=5, color=['blue', 'orange'])
ax[0].set_title('Mean Accuracy with Standard Deviation')
ax[0].set_ylabel('Accuracy')
ax[0].set_ylim(0, 100)  # Assuming accuracy is between 0 and 1

# Plotting Time
ax[1].bar(categories, data['Mean Time'], yerr=data['Std Time'], capsize=5, color=['green', 'red'])
ax[1].set_title('Mean Time with Standard Deviation')
ax[1].set_ylabel('Time (Seconds)')
ax[1].set_ylim(0, 120)

# Display the plot
plt.tight_layout()
plt.show()

# %%
