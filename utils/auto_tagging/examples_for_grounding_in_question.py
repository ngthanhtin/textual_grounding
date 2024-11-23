examples_for_grounding_in_question = """
# EXAMPLES
Below are examples of questions before and after key phrases are tagged using <fact> tags.
If one key phrase was absent, it would be impossible for one to answer the question correctly.

## Question 1: 
### BEFORE: 
Sam works at the Widget Factory, assembling Widgets. He can assemble 1 widget every 10 minutes. Jack from the loading dock can help assemble widgets when he doesn't have anything else to do. When he helps, they put together 2 complete widgets every 15 minutes. Recently the factory hired Tony to help assemble widgets. Being new to the job, he doesn't work as fast as Sam or Jack. Yesterday Sam worked for 6 hours before he had to leave work early for a dentist appointment. Jack was able to help out for 4 hours before he had to go back to the loading dock to unload a new shipment of widget materials. Tony worked the entire 8-hour shift. At the end of the day, they had completed 68 widgets. How long does it take Tony to assemble a Widget, in minutes?

### AFTER:
Sam works at the Widget Factory, assembling Widgets. He can assemble <fact1>1 widget every 10 minutes</fact1>. Jack from the loading dock can help assemble widgets when he doesn't have anything else to do. When he helps, they put together <fact2>2 complete widgets every 15 minutes</fact2>. Recently the factory hired Tony to help assemble widgets. Being new to the job, he doesn't work as fast as Sam or Jack. Yesterday Sam worked for <fact3>6 hours</fact3> before he had to leave work early for a dentist appointment. Jack was able to help out for <fact4>4 hours</fact4> before he had to go back to the loading dock to unload a new shipment of widget materials. Tony worked the entire <fact5>8-hour shift</fact5>. At the end of the day, they had completed <fact6>68 widgets</fact6>. How long does it take Tony to assemble a Widget, in minutes?


## Question 2: 
### BEFORE: 
For every 12 cans you recycle, you receive $0.50, and for every 5 kilograms of newspapers, you receive $1.50. If your family collected 144 cans and 20 kilograms of newspapers, how much money would you receive?

### AFTER: 
For <fact1>every 12 cans</fact1> you recycle, you receive <fact2>$0.50</fact2>, and for <fact3>every 5 kilograms of newspapers</fact3>, you receive <fact4>$1.50</fact4>. If your family collected <fact5>144 cans</fact5> and <fact6>20 kilograms of newspapers</fact6>, how much money would you receive?

## Question 3: 
### BEFORE: 
At a presentation about post traumatic stress disorder, would Ariana Grande be a topic of relevance?

### AFTER: 
At a presentation about <fact1>post traumatic stress disorder</fact1>, would <fact2>Ariana Grande</fact2> be a topic of relevance?

## Question 4: 
### BEFORE: 
Has the Indian Ocean garbage patch not completed two full rotations of debris since its discovery?

### AFTER:
Has the <fact1>Indian Ocean garbage patch</fact1> <fact2>not</fact2> completed <fact3>two full rotations</fact3> of debris since its discovery?

## Question 5: 
### BEFORE:
The following paragraphs each describe a set of seven objects arranged in a fixed order. The statements are logically consistent within each paragraph. In a golf tournament, there were seven golfers: Ana, Eve, Ada, Dan, Rob, Amy, and Joe. Dan finished third. Ana finished above Ada. Amy finished last. Dan finished below Rob. Eve finished below Ada. Rob finished below Joe. Choose one correct option: (A) Ana finished third (B) Eve finished third (C) Ada finished third (D) Dan finished third (E) Rob finished third (F) Amy finished third (G) Joe finished third

### AFTER:
The following paragraphs each describe a set of seven objects arranged in a fixed order. The statements are logically consistent within each paragraph. In a golf tournament, there were seven golfers: Ana, Eve, Ada, Dan, Rob, Amy, and Joe. <fact1>Dan finished third</fact1>. Ana finished above Ada. Amy finished last. Dan finished below Rob. Eve finished below Ada. Rob finished below Joe. Choose one correct option: (A) Ana finished third (B) Eve finished third (C) Ada finished third (D) <fact1>Dan finished third</fact1> (E) Rob finished third (F) Amy finished third (G) Joe finished third

## Question 6: 
### BEFORE:
The following paragraphs each describe a set of seven objects arranged in a fixed order. The statements are logically consistent within each paragraph. In a golf tournament, there were seven golfers: Eve, Mya, Rob, Ana, Ada, Mel, and Joe. Eve finished third. Mya finished above Joe. Mel finished above Ada. Mya finished above Rob. Mel finished below Joe. Mya finished second. Ada finished second-to-last. Options: (A) Eve finished last (B) Mya finished last (C) Rob finished last (D) Ana finished last (E) Ada finished last (F) Mel finished last (G) Joe finished last

### AFTER:
The following paragraphs each describe a set of seven objects arranged in a fixed order. The statements are logically consistent within each paragraph. In a golf tournament, there were seven golfers: Eve, Mya, Rob, Ana, Ada, Mel, and Joe. <fact1>Eve finished third</fact1>. <fact2>Mya finished above Joe<fact2>. <fact3>Mel finished above Ada</fact3>. <fact4>Mya finished above Rob</fact4>. <fact5>Mel finished below Joe</fact5>. <fact6>Mya finished second</fact6>. <fact7>Ada finished second-to-last</fact7>. Options: (A) Eve finished last (B) Mya finished last (C) Rob finished last (D) Ana finished last (E) Ada finished last (F) Mel finished last (G) Joe finished last

## Question 7:
### BEFORE:
How would a typical person answer each of the following questions about causation? A machine is set up in such a way that it will short circuit if both the black wire and the red wire touch the battery at the same time. The machine will not short circuit if just one of these wires touches the battery. The black wire is designated as the one that is supposed to touch the battery, while the red wire is supposed to remain in some other part of the machine. One day, the black wire and the red wire both end up touching the battery at the same time. There is a short circuit. Did the black wire cause the short circuit? Options: - Yes - No

### AFTER:
How would a typical person answer each of the following questions about causation? A machine is set up in such a way that it will <fact1>short circuit if both the black wire and the red wire touch the battery</fact1> at the same time. The machine will <fact2>not short circuit if just one of these wires touches the battery</fact2>. The black wire is designated as the one that is supposed to touch the battery, while the red wire is supposed to remain in some other part of the machine. One day, the <fact1>red wire and the black wire both end up touching</fact1> the battery at the same time. There is a short circuit. Did the black wire cause the short circuit?
Options: - Yes - No

## Question 8:
### BEFORE:
A coin is heads up. roxas does not flip the coin. scheideman does not flip the coin.  Is the coin still heads up? Flip means reverse.

### AFTER:
<fact1>A coin is heads up</fact1>. roxas does <fact2>not flip</fact2> the coin. scheideman does <fact3>not flip</fact3> the coin.  Is the coin still heads up? Flip means reverse.

## Question 9:
### BEFORE:
I have four pianos, four snails, three chickens, a pig, a dog, and two cows. How many animals do I have?

### AFTER:
I have four pianos, <fact1>four snails</fact1>, <fact2>three chickens</fact2>, <fact3>a pig</fact3>, <fact4>a dog</fact4>, and <fact5>two cows</fact5>. How many <fact6>animals</fact6> do I have?

## Question 10:
### BEFORE:
2015 is coming in 36 hours. What is the date one week from today in MM/DD/YYYY?

### AFTER:
<fact1>2015</fact1> is coming in <fact2>36 hours</fact2>. What is the date <fact3>one week from today</fact3> in MM/DD/YYYY?

## Question 11:
### BEFORE:
If you follow these instructions, do you return to the starting point? Always face forward. Take 1 step right. Take 3 steps left. Take 2 steps right. Options: - Yes - No

### AFTER:
If you follow these instructions, do you return to the starting point? Always face forward. Take <fact1>1 step right</fact1>. Take <fact2>3 steps left</fact2>. Take <fact3>2 steps right</fact3>. Options: - Yes - No

## Question 12:
### BEFORE:
Question: On the desk, you see a set of things arranged in a row: a grey cup, a purple mug, and a blue teddy bear. What is the color of the thing directly to the right of the cup? Options: (A) red (B) orange (C) yellow (D) green (E) blue (F) brown (G) magenta (H) fuchsia (I) mauve (J) teal (K) turquoise (L) burgundy (M) silver (N) gold (O) black (P) grey (Q) purple (R) pink

### AFTER:
On the desk, you see a set of things arranged in a row: a <fact1>grey cup</fact1>, a <fact2>purple mug</fact2>, and a blue teddy bear. What is <fact3>the color of the thing directly to the right of the cup</fact3>? Options: (A) red (B) orange (C) yellow (D) green (E) blue (F) brown (G) magenta (H) fuchsia (I) mauve (J) teal (K) turquoise (L) burgundy (M) silver (N) gold (O) black (P) grey (Q) purple (R) pink

## Question 13:
### BEFORE:
Among the various models of Delta vacuum cleaners, one cannot accurately predict how effectively a particular model cleans simply by determining how powerful its motor is. The efficiency of dust filtration systems varies significantly, even between models of Delta vacuum cleaners equipped with identically powerful motors. The argument's conclusion is properly drawn if which one of the following is assumed?
Answer Choices:
(a) All Delta vacuum cleaners that clean equally effectively have identically powerful motors.
(b) One cannot accurately assess how effectively any Delta vacuum cleaner cleans without knowing how powerful that vacuum cleaner's motor is.
(c) For each Delta vacuum cleaner, the efficiency of its dust filtration system has a significant impact on how effectively it cleans.
(d) For any two Delta vacuum cleaners with equally efficient dust filtration systems, the one with the more powerful motor cleans more effectively.

### AFTER:
Among the various models of Delta vacuum cleaners, <fact1>one cannot accurately predict how effectively a particular model cleans</fact1> simply by <fact2>determining how powerful its motor is</fact2>. The efficiency of <fact3>dust filtration systems varies significantly</fact3>, even between models of <fact4>Delta vacuum cleaners equipped with identically powerful motors</fact4>. The argument's conclusion is properly drawn if which one of the following is assumed?
(a) All Delta vacuum cleaners that clean equally effectively have identically powerful motors.
(b) One cannot accurately assess how effectively any Delta vacuum cleaner cleans without knowing how powerful that vacuum cleaner's motor is.
(c) For each Delta vacuum cleaner, the efficiency of its dust filtration system has a significant impact on how effectively it cleans.
(d) For any two Delta vacuum cleaners with equally efficient dust filtration systems, the one with the more powerful motor cleans more effectively.

## Question 14:
### BEFORE:
We have three blocks, A, B and C. Block A has a medium blue square. Below block A is block B which has one medium black square. To the left of block B there is block C which has two medium blue squares. Medium blue square number one is below medium blue square number two. A medium yellow square is below medium blue square number two and medium blue square number one. What is to the left of the black thing? a medium blue square that is in block A or a medium blue square number two?
(a) medium blue square  that is in block A
(b) medium blue square  number two
(c) both of them
(d) none of them

### AFTER:
We have three blocks, A, B, and C. <fact1>Block A has a medium blue square</fact1>. <fact2>Below block A is block B, which has one medium black square</fact2>. <fact3>To the left of block B, there is block C, which has two medium blue squares</fact3>. Medium blue square number one is below <fact4>medium blue square number two</fact4>. A medium yellow square is below medium blue square number two and medium blue square number one. What is to the left of the black thing? <fact1>A medium blue square that is in block A</fact1> or <fact4>a medium blue square number two</fact4>?

## Question 15:
### BEFORE:
"""

instruction_for_grounding_in_question = 'Read the question and insert the tags into the question via the following rules:\
1. Insert only tags keeping the original words unchanged.\
2. Put the tags (e.g., <fact1></fact1>, <fact2></fact2>) around the shortest and most concise important phrases.\
3. A phrase is considered important and should be tagged if replacing that phrase by a closest alternative phrase would change the answer. \
4. Do not tag phrases non-important to answering the question.\
Re-generate the question after adding tags to the phrases:\
### AFTER: '


# 5. If two or more facts are consecutive and cannot be meaningfully split, tag them together. \
#  The irrelevant key phrases are phrases that are not used to answer the question.


