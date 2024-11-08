# %%
import re

# Function to extract information from tags
def extract_info(text, tag):
    pattern = f'<{tag}>(.*?)</{tag}>'
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1) if match else None

# The tagged text (this would be the editable part for the user)
tagged_text = """
<a>Sam works at the Widget Factory, assembling Widgets. He can assemble 1 widget every 10 minutes.</a>
<b>Jack from the loading dock can help assemble widgets when he doesn't have anything else to do. When he helps, they put together 2 complete widgets every 15 minutes.</b>
<c>Recently the factory hired Tony to help assemble widgets. Being new to the job, he doesn't work as fast as Sam or Jack.</c>
<d>Yesterday Sam worked for 5 hours</d>
<e>Jack was able to help out for 4 hours</e>
<f>Tony worked the entire 8-hour shift.</f>
<g>they had completed 68 widgets.</g>
The final answer is
"""
# GT: 30 minutes

# Extract information from tags
sam_info = extract_info(tagged_text, 'a')
jack_info = extract_info(tagged_text, 'b')
sam_time = extract_info(tagged_text, 'd')
jack_time = extract_info(tagged_text, 'e')
tony_time = extract_info(tagged_text, 'f')
total_widgets = extract_info(tagged_text, 'g')

# Parse the extracted information
SAM_WIDGET_TIME = int(re.search(r'(\d+) minutes', sam_info).group(1))
JACK_WIDGET_TIME = int(re.search(r'(\d+) minutes', jack_info).group(1))
sam_work_time = int(re.search(r'(\d+) hours', sam_time).group(1)) * 60
jack_work_time = int(re.search(r'(\d+) hours', jack_time).group(1)) * 60
tony_work_time = int(re.search(r'(\d+)-hour', tony_time).group(1)) * 60
total_widgets = int(re.search(r'(\d+) widgets', total_widgets).group(1))

# Calculate widgets made by Sam and Jack
sam_widgets = sam_work_time // SAM_WIDGET_TIME
jack_widgets = jack_work_time // JACK_WIDGET_TIME

# Calculate widgets made by Tony
tony_widgets = total_widgets - sam_widgets - jack_widgets

# Calculate Tony's time per widget
tony_widget_time = tony_work_time // tony_widgets

print(f"Sam made {sam_widgets} widgets")
print(f"Jack made {jack_widgets} widgets")
print(f"Tony made {tony_widgets} widgets")
print(f"It takes Tony {tony_widget_time} minutes to assemble one widget")
# %%
