<div align="center">    
 
# HoT: Highlighted Chain of Thought for Referencing Supportive Facts from Inputs
by [Tin Nguyen](https://ngthanhtin.github.io/), [Logan Bolton](), and [Anh Nguyen](https://anhnguyen.me/). 
</div> 

<i>
_**tldr:** An Achilles heel of Large Language Models (LLMs) is their tendency to hallucinate non-factual statements. A response mixed of factual and non-factual statements poses a challenge for humans to verify and accurately base their decisions on. To combat this problem, we propose Highlighted Chain-of-Thought Prompting (HoT), a technique for prompting LLMs to generate responses with XML-tags that ground facts to those provided in the query. That is, given an input question, LLMs would first re-format the question to add XML tags highlighting key facts, and then, generate a response with highlights over the facts referenced from the input. Interestingly, in few-shot settings, HoT **outperforms** the vanilla chain of thoughts (CoT) on a wide range of 17 tasks from arithmetic, reading comprehension to logical reasoning.
</i>

# 1. Requirements
```
python=3.10.15
google-generativeai==0.8.3
openai==1.58.1
```

# 2. How to run
```
main.py
```

# 3. How to evaluate the result

# 4. How to visualize the result
```
visualize.py
```

# 5. Human Study





